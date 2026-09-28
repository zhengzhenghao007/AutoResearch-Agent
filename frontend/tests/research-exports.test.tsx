import { afterEach, beforeEach, expect, test, vi } from 'vitest';
import { act, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ResearchExports from '@/components/ResearchExports';
import { researchApi } from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{citations:vi.fn(),bibtex:vi.fn()}}));
const id='a'.repeat(32);
const registry={schema_version:1 as const,run_id:id,topic:'Navigation',sources:[]};
beforeEach(()=>{vi.resetAllMocks();vi.mocked(researchApi.citations).mockResolvedValue(registry);vi.mocked(researchApi.bibtex).mockResolvedValue({run_id:id,bibtex:'@misc{safe,\n}\n',skipped_sources:[]});});
afterEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals();});

test('loads independently and downloads exact backend text with safe filenames',async()=>{
  const urls=vi.fn().mockReturnValue('blob:test');const revoke=vi.fn();
  vi.stubGlobal('URL',Object.assign(URL,{createObjectURL:urls,revokeObjectURL:revoke}));
  const downloads:string[]=[];
  vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(function(this: HTMLAnchorElement){downloads.push(this.download);});
  render(<ResearchExports runId={id}/>);
  expect(researchApi.citations).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Load citation JSON'}));
  await screen.findByText('No processed sources are available for citation export.');
  await userEvent.click(screen.getByRole('button',{name:'Download citation JSON'}));
  expect(downloads[0]).toBe(`citations-${id}.json`);
  const jsonBlob=urls.mock.calls[0][0] as Blob;
  expect(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsText(jsonBlob);})).toBe(JSON.stringify(registry,null,2)+'\n');
  await userEvent.click(screen.getByRole('button',{name:'Load BibTeX'}));
  await screen.findByText('@misc{safe, }');
  await userEvent.click(screen.getByRole('button',{name:'Download BibTeX'}));
  const bibBlob=urls.mock.calls[1][0] as Blob;
  expect(await new Promise(resolve=>{const r=new FileReader();r.onload=()=>resolve(r.result);r.readAsText(bibBlob);})).toBe('@misc{safe,\n}\n');
  expect(downloads[1]).toBe(`references-${id}.bib`);
});

test('failure in citations does not hide BibTeX skips or empty state',async()=>{
  vi.mocked(researchApi.citations).mockRejectedValue(new Error('Source unavailable'));
  vi.mocked(researchApi.bibtex).mockResolvedValue({run_id:id,bibtex:'',skipped_sources:[{source_id:'local',reason:'missing_bibliographic_identity'}]});
  render(<ResearchExports runId={id}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load citation JSON'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Source unavailable');
  await userEvent.click(screen.getByRole('button',{name:'Load BibTeX'}));
  await screen.findByText('No sources could be exported to BibTeX.');
  expect(screen.getByText(/local: Missing bibliographic identity/)).toBeInTheDocument();
  expect(screen.queryByRole('button',{name:'Download BibTeX'})).not.toBeInTheDocument();
});

test.each(['citations','bibtex'] as const)('ignores delayed %s response after record switch',async(kind)=>{
  let resolve!:(v:never)=>void;
  vi.mocked(researchApi[kind]).mockReturnValueOnce(new Promise(r=>{resolve=r;}) as never);
  const {rerender}=render(<ResearchExports runId={id}/>);
  await userEvent.click(screen.getByRole('button',{name:kind==='citations'?'Load citation JSON':'Load BibTeX'}));
  expect(screen.getByRole('status')).toBeInTheDocument();
  rerender(<ResearchExports runId={'b'.repeat(32)}/>);
  await act(async()=>resolve((kind==='citations'?registry:{run_id:id,bibtex:'STALE',skipped_sources:[]}) as never));
  expect(screen.queryByText(/STALE|Navigation/)).not.toBeInTheDocument();
  expect(screen.queryByRole('status')).not.toBeInTheDocument();
});

test('empty BibTeX without skips reports no processed sources',async()=>{
  vi.mocked(researchApi.bibtex).mockResolvedValue({run_id:id,bibtex:'',skipped_sources:[]});
  render(<ResearchExports runId={id}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load BibTeX'}));
  await screen.findByText('No processed sources are available for BibTeX export.');
});

test('same-record revision clears previous exports and errors',async()=>{
  const {rerender}=render(<ResearchExports runId={id} revision={1}/>);
  await userEvent.click(screen.getByRole('button',{name:'Load citation JSON'}));
  await screen.findByRole('button',{name:'Download citation JSON'});
  vi.mocked(researchApi.bibtex).mockRejectedValue(new Error('Old failure'));
  await userEvent.click(screen.getByRole('button',{name:'Load BibTeX'}));
  await screen.findByText('Old failure');
  rerender(<ResearchExports runId={id} revision={2}/>);
  expect(screen.queryByRole('button',{name:'Download citation JSON'})).not.toBeInTheDocument();
  expect(screen.queryByText('Old failure')).not.toBeInTheDocument();
});
