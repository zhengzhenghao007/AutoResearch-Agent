import type {ManuscriptDraftData} from './manuscript-draft';
import type {SearchBatch} from './metadata-search';
export interface LiteraturePacket {report:{run_id:string;project_name:string;goal:string;input_sha256:string;generated_at:string;source_ids:string[];sections:ManuscriptDraftData['sections'];searches:SearchBatch[];missing_requirements:string[];scope:string};markdown:string}
