import { expect, test } from 'vitest';
import { sourcePdf } from '@/components/EvidenceViewer';
test('only canonical HTTPS arXiv PDF sources become external links',()=>{
  expect(sourcePdf('https://arxiv.org/pdf/2401.12345v2',3)).toBe('https://arxiv.org/pdf/2401.12345v2#page=3');
  for(const uri of ['upload://paper.pdf','javascript:alert(1)','https://arxiv.org.evil.test/pdf/2401.12345','https://user@arxiv.org/pdf/2401.12345','http://arxiv.org/pdf/2401.12345','https://arxiv.org/pdf/2401.12345?redirect=evil'])expect(sourcePdf(uri,1)).toBeNull();
});
