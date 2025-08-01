import re

from django import forms

from posts.models import Post
import bleach

ALLOWED_TAGS = ["a", "code", "i", "strong"]

class PostForm(forms.ModelForm):
    def clean_text(self):
        raw = self.cleaned_data["text"].strip()

        tags = [m.lower() for m in re.findall(r"</?([a-z][a-z0-9]*)\b", raw)]
        disallowed = set(tags) - set(ALLOWED_TAGS)

        if disallowed:
            raise forms.ValidationError(f"Недопустимые HTML-теги: {', '.join(disallowed)}")

        return bleach.clean(
            raw,
            tags=ALLOWED_TAGS,
            strip=True
        )

    class Meta:
        model = Post
        fields = ["text", "image"]
        widgets = {
            "text": forms.Textarea(attrs={
                "rows": 5,
                "cols": 40,
                "class": "text-area-public",
                "style": "width: 100%",
            }),
        }
        help_texts = {
            "text": "Разрешены HTML-теги: &lt;a href="" title=""&gt;&lt;/a&gt;, &lt;code&gt;&lt;/code&gt;, &lt;i&gt;&lt;/i&gt;, &lt;strong&gt;&lt;/strong&gt;"
        }