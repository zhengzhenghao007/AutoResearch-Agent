import type {ResearchRun} from '@/types/research';

export function projectName(run: Pick<ResearchRun,'topic'|'project_name'|'effective_project_name'>): string {
  return run.project_name || run.effective_project_name || (/\.pdf$/i.test(run.topic) ? 'Research' : run.topic) || 'Research';
}
