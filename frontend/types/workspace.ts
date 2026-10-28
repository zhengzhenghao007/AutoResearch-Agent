export interface WorkspaceItemRequest {
  kind: 'note' | 'table' | 'figure';
  title: string;
  text: string;
  dataset_id: string | null;
  columns: string[];
  x_column: string | null;
  chart_type: 'bar' | 'line' | 'scatter';
}
export interface WorkspaceItem extends WorkspaceItemRequest {
  id: string;
  created_at: string;
  dataset_sha256: string | null;
}
export interface WorkspacePreview {
  item: WorkspaceItemRequest;
  dataset_sha256: string | null;
  headers: string[];
  rows: (string | number | null)[][];
  svg: string | null;
  markdown: string;
  warnings: string[];
}
