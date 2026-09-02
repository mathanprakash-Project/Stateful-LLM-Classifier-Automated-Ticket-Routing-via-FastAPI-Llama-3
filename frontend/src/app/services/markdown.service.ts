import { Injectable, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

@Injectable({ providedIn: 'root' })
export class MarkdownService {
  private sanitizer = inject(DomSanitizer);

  constructor() {
    marked.setOptions({
      gfm: true,
      breaks: true,
    });
  }

  render(markdownText: string): SafeHtml {
    if (!markdownText) return '';
    try {
      const rawHtml = marked.parse(markdownText) as string;
      const cleanHtml = DOMPurify.sanitize(rawHtml);
      return this.sanitizer.bypassSecurityTrustHtml(cleanHtml);
    } catch (e) {
      console.error('Error parsing markdown with marked:', e);
      return markdownText;
    }
  }
}
