import {afterEach,expect,test,vi} from 'vitest';
import {act,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ManuscriptDraft from '@/components/ManuscriptDraft';
import {researchApi} from '@/lib/research-api';
vi.mock('@/lib/research-api',()=>({researchApi:{manuscriptDraft:vi.fn()}}));
const draft={schema_version:1 as const,builder:'evidence-draft-v1' as const,run_id:'a'.repeat(32),topic:'Study',input_sha256:'b'.repeat(64),sections:[{id:'user_results',title:'User observations',purpose:'Describe user data.',blocks:[{id:'missing:user_results',kind:'placeholder' as const,text:'No user experimental observations were supplied.',paper:null,computation:null}]}],omitted_legacy_observation_claims:0,scientific_validation:'not_assessed' as const,contradiction_review:'not_assessed' as const,approval:'not_requested' as const,statistics_scope:'No inference.',scope:'Read-only draft; not approved for publication.'};
afterEach(()=>{vi.resetAllMocks();});

test('loads only on request and shows missing data and unassessed review states',async()=>{
  vi.mocked(researchApi.manuscriptDraft).mockResolvedValue(draft);
  render(<ManuscriptDraft runId={draft.run_id} revision={0}/>);
  expect(researchApi.manuscriptDraft).not.toHaveBeenCalled();
  await userEvent.click(screen.getByRole('button',{name:'Preview chapter draft'}));
  expect(await screen.findByText(draft.sections[0].blocks[0].text)).toBeInTheDocument();
  expect(screen.getByText(/Contradiction review: not assessed/)).toBeInTheDocument();
  expect(screen.getByText(draft.scope)).toBeInTheDocument();
  expect(screen.queryByRole('button',{name:/export/i})).not.toBeInTheDocument();
});

test('revision discards delayed responses',async()=>{
  let resolve!:(value:typeof draft)=>void;
  vi.mocked(researchApi.manuscriptDraft).mockReturnValue(new Promise(r=>{resolve=r;}));
  const {rerender}=render(<ManuscriptDraft runId={draft.run_id} revision={0}/>);
  await userEvent.click(screen.getByRole('button',{name:'Preview chapter draft'}));
  rerender(<ManuscriptDraft runId={draft.run_id} revision={1}/>);
  await act(async()=>resolve(draft));
  expect(screen.queryByText(draft.scope)).not.toBeInTheDocument();
});

test('wrong record response fails visibly and can be retried',async()=>{
  vi.mocked(researchApi.manuscriptDraft).mockResolvedValueOnce({...draft,run_id:'wrong'}).mockResolvedValueOnce(draft);
  render(<ManuscriptDraft runId={draft.run_id} revision={0}/>);
  await userEvent.click(screen.getByRole('button',{name:'Preview chapter draft'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('different record');
  await userEvent.click(screen.getByRole('button',{name:'Preview chapter draft'}));
  expect(await screen.findByText(draft.scope)).toBeInTheDocument();
});
