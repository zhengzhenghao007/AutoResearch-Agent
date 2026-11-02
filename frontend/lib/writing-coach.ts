import type {ManuscriptSection} from '@/types/manuscript';
import type {DraftBlock} from '@/types/manuscript-draft';

export type ResearchApproach='unspecified'|'empirical'|'theory'|'review'|'interpretive';
export interface CoachingIssue {
 code:string;priority:'repair'|'develop'|'consider';title:string;action:string;
 sectionId?:string;sentenceId?:string;excerpt?:string;
}
const questions:Record<ResearchApproach,string[]>={
 unspecified:['What kind of evidence would answer your question: observations, a proof, a literature synthesis or an interpretation? Choose an approach to refine these prompts.'],
 empirical:['Which baseline or control isolates the proposed explanation, and what would falsify it?', 'Do the protocol, sample, units, missing data and uncertainty justify the comparison?', 'Which figure answers each research question, and are its source data and transformation recorded?'],
 theory:['Which assumptions does each proof require, and where does the argument fail without them?', 'What counterexample tests the boundary of the theorem?', 'What follows from the theorem, and what remains conjecture rather than a proved result?'],
 review:['What search scope and inclusion criteria determine which studies enter the synthesis?', 'Which studies disagree, and can differences in setting or measurement explain the disagreement?', 'What does the collection support, and what remains unknown because of missing or excluded literature?'],
 interpretive:['Why are these texts, cases or archives appropriate for the question?', 'Which alternative interpretation challenges the thesis, and how does the material distinguish them?', 'Are the core concepts used consistently, and does the conclusion stay within the material’s scope?'],
};

export function buildWritingCoach(sections:ManuscriptSection[],blocks:DraftBlock[],stale:boolean,approach:ResearchApproach){
 const issues:CoachingIssue[]=[];
 if(stale)issues.push({code:'stale_sources',priority:'repair',title:'Source snapshot changed',action:'Refresh or reconcile the manuscript references before relying on their bindings.'});
 if(!sections.length)issues.push({code:'empty_draft',priority:'develop',title:'No chapters yet',action:'Initialize a manuscript, then identify its question and intended contribution.'});
 for(const section of sections){
  if(!section.sentences.length)issues.push({code:'empty_chapter',priority:'develop',title:`Empty chapter: ${section.title}`,sectionId:section.id,action:'Write the purpose of this chapter and the evidence it needs, or remove it.'});
  for(const sentence of section.sentences){
   const location={sectionId:section.id,sentenceId:sentence.id,excerpt:sentence.text.slice(0,240)};
   const add=(code:string,priority:CoachingIssue['priority'],title:string,action:string)=>issues.push({code,priority,title,action,...location});
   if(sentence.kind==='placeholder')add('placeholder','develop','Unresolved writing task','Supply the missing material or explicitly narrow the paper’s scope; do not invent a result.');
   const required:Partial<Record<typeof sentence.kind,DraftBlock['kind']>>={paper_report:'paper_claim',user_observation:'user_statistics',research_asset:'research_asset'};
   const expected=required[sentence.kind];
   if(expected&&!sentence.reference_ids.length)add('missing_reference','repair','Factual paragraph has no reference','Choose the saved source or calculation that supports this paragraph. A reference alone still requires semantic checking.');
   for(const id of sentence.reference_ids){
    const matches=blocks.filter(b=>b.id===id);
    if(matches.length!==1)add('missing_binding','repair','Reference is missing or ambiguous',`Resolve reference ${id} against the current manuscript source snapshot.`);
    else if(expected&&matches[0].kind!==expected)add('reference_kind','repair','Reference type does not match the paragraph',`Use ${expected.replaceAll('_',' ')} material for this paragraph, or correct its type after checking the claim.`);
   }
   if(['paper_report','user_observation'].includes(sentence.kind)&&/\b(proves?|always|never|guarantees?|all cases|state.of.the.art)\b|证明了|始终|从不|所有情况|最先进/i.test(sentence.text))
    add('claim_strength','consider','Check the scope of a strong claim','Language cue only: compare this wording with the assumptions, population and uncertainty in the cited evidence. It may be justified; this check cannot decide.');
  }
 }
 const order={repair:0,develop:1,consider:2};issues.sort((a,b)=>order[a.priority]-order[b.priority]);
 return {scientificValidation:'not_assessed' as const,approach,issues,questions:[
  'What precise question does the paper answer, and why does that answer matter?',
  'Which limitation of prior work motivates the approach, and which saved sources establish that limitation?',
  'For each claimed contribution, which chapter and evidence demonstrate it, and what alternative explanation remains?',
  ...questions[approach],
  'What is the next smallest research or writing action that would resolve the most important uncertainty?',
 ]};
}
