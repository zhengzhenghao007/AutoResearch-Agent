import {afterEach,beforeEach,expect,test,vi} from 'vitest';
import {act,render,screen,within} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SourceDuplicateClues from '@/components/SourceDuplicateClues';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{sourceDuplicates:vi.fn()}}));
const id='a'.repeat(32);
const empty={schema_version:1 as const,run_id:id,groups:[],candidate_source_links:[]};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(researchApi.sourceDuplicates).mockResolvedValue(empty);});
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();});
test('loads empty report on demand and downloads unchanged JSON',async()=>{
  const create=vi.fn().mockReturnValue('blob:test');vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:create,revokeObjectURL:vi.fn()}));
  let filename='';vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this:HTMLAnchorElement){filename=this.download;});
  render(<SourceDuplicateClues runId={id} revision={0}/>);expect(researchApi.sourceDuplicates).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Load duplicate clues'}));
  expect(await screen.findByText('No duplicate groups found.')).toBeInTheDocument();
  expect(screen.getByText('No candidate-source links found.')).toBeInTheDocument();
  await userEvent.click(screen.getByRole('button',{name:'Download duplicate clues JSON'}));
  expect(filename).toBe(`source-duplicates-${id}.json`);
  const blob=create.mock.calls[0][0] as Blob;
  expect(await new Promise(resolve=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result);reader.readAsText(blob);})).toBe(JSON.stringify(empty,null,2)+'\n');
});
test('renders distinct clue meanings and links without making unsafe URLs clickable',async()=>{
  const members=[{entity_type:'candidate' as const,entity_id:'a',title:'<script>danger</script>',uri:'javascript:alert(1)'},{entity_type:'candidate' as const,entity_id:'b',title:'Second',uri:'https://arxiv.org/pdf/2401.12345v1'}];
  vi.mocked(researchApi.sourceDuplicates).mockResolvedValue({...empty,groups:[{kind:'exact_arxiv_identifier',identity_status:'explicit_identifier',identity_value:'2401.12345v1',members},{kind:'same_pdf_bytes',identity_status:'exact_content_hash',identity_value:'0'.repeat(64),members:members.map(m=>({...m,entity_type:'processed_source'}))},{kind:'shared_user_supplied_doi',identity_status:'user_supplied_unverified',identity_value:'10.1234/test',members:members.map(m=>({...m,entity_type:'processed_source'}))}],candidate_source_links:[{candidate_id:'a',source_id:'source',arxiv_identifier:'2401.12345v1'}]});
  render(<SourceDuplicateClues runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load duplicate clues'}));
  await screen.findByRole('heading',{name:'Exact arXiv identifier'});expect(screen.getByRole('heading',{name:'Matching stored PDF hash'})).toBeInTheDocument();expect(screen.getByRole('heading',{name:'Shared user-supplied DOI'})).toBeInTheDocument();
  expect(screen.getByText(/not revalidated/)).toBeInTheDocument();expect(screen.getByText(/Not externally verified/)).toBeInTheDocument();
  expect(within(screen.getByRole('region',{name:'Candidate-source links'})).getByText('Candidate a → source source; arXiv 2401.12345v1')).toBeInTheDocument();
  expect(screen.queryAllByRole('link')).toHaveLength(0);expect(document.querySelector('script')).toBeNull();
});
test.each(['record','revision'])('ignores delayed reads after a %s change',async(change)=>{
  let resolve!:(value:typeof empty)=>void;vi.mocked(researchApi.sourceDuplicates).mockReturnValueOnce(new Promise(r=>{resolve=r;}));
  const {rerender}=render(<SourceDuplicateClues runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load duplicate clues'}));
  rerender(<SourceDuplicateClues runId={change==='record'?'b'.repeat(32):id} revision={1}/>);
  await act(async()=>resolve(empty));expect(screen.queryByRole('button',{name:'Download duplicate clues JSON'})).not.toBeInTheDocument();
});
test('mismatched response is rejected and manual retry recovers',async()=>{
  vi.mocked(researchApi.sourceDuplicates).mockResolvedValueOnce({...empty,run_id:'wrong'});
  render(<SourceDuplicateClues runId={id} revision={0}/>);await userEvent.click(screen.getByRole('button',{name:'Load duplicate clues'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('different research record');
  expect(researchApi.sourceDuplicates).toHaveBeenCalledTimes(1);
  await userEvent.click(screen.getByRole('button',{name:'Load duplicate clues'}));await screen.findByText('No duplicate groups found.');
});
