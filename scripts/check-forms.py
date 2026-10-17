#!/usr/bin/env python3
"""Refuse unexpected forms or submission targets in the generated site."""
from html.parser import HTMLParser
from pathlib import Path
import sys


class Forms(HTMLParser):
    def __init__(self, controls_outside=False):
        super().__init__(convert_charrefs=True)
        self.forms = []
        self.current = None
        # The web installer's buttons and file inputs submit nothing. It may have no form either.
        self.controls_outside = controls_outside

    def handle_starttag(self, tag, attrs):
        if tag == 'form':
            if self.current is not None:
                raise ValueError('nested form')
            self.current = [attrs, []]
            self.forms.append(self.current)
        elif tag in {'input', 'textarea', 'button', 'select'}:
            if self.current is None:
                if self.controls_outside:
                    return
                raise ValueError('form control outside the contact form')
            self.current[1].append((tag, attrs))

    def handle_endtag(self, tag):
        if tag == 'form':
            if self.current is None:
                raise ValueError('unexpected form end')
            self.current = None


def validate(root):
    count = 0
    for path in sorted(root.rglob('*.html')):
        value = Forms(path.relative_to(root).as_posix().startswith('install/web/'))
        value.feed(path.read_text(encoding='utf-8'))
        if value.current is not None:
            raise ValueError('unclosed form')
        for attrs, controls in value.forms:
            count += 1
            fields = dict(attrs)
            if len(fields) != len(attrs) or fields != {
                'class': 'contact-form', 'action': '/contact/submit', 'method': 'post',
                'accept-charset': 'UTF-8', 'aria-labelledby': 'contact',
            } or path.relative_to(root).as_posix() != 'about/index.html':
                raise ValueError('unexpected form or submission target')
            if [tag for tag, _ in controls] != ['input', 'textarea', 'button']:
                raise ValueError('unexpected contact controls')
            for (tag, pairs), expected in zip(controls, [
                {'id': 'contact-email', 'name': 'email', 'type': 'email',
                 'maxlength': '254', 'required': None},
                {'id': 'contact-message', 'name': 'message', 'maxlength': '4000',
                 'required': None},
                {'type': 'submit'},
            ]):
                actual = dict(pairs)
                if len(actual) != len(pairs) or any(actual.get(k) != v or k not in actual
                                                   for k, v in expected.items()):
                    raise ValueError('contact control contract differs')
                if any(k.startswith('form') for k in actual) or tag == 'select':
                    raise ValueError('submission override')
    if count != 1:
        raise ValueError('expected one contact form')


if __name__ == '__main__':
    try:
        validate(Path(sys.argv[1]))
    except (ValueError, OSError, IndexError):
        raise SystemExit('Contact form check failed.')
    print('ok    one bounded, same-origin contact form')
