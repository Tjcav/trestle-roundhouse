#!/usr/bin/env bash
set -euo pipefail

echo "Paste Copilot plan. Finish with Ctrl-D:"
PLAN=$(cat)

PROMPT=$(cat <<EOF
You are a custodian AI.

Your job:
- Detect scope creep
- Detect violations of user preferences
- Detect large or risky changes
- Keep feedback short

User rules:
- Do not expand scope unless explicitly asked
- Avoid inventing architecture
- Prefer small, boring solutions
- Avoid large diffs or multi-file rewrites
- If something feels heavy, flag it

Plan to review:
$PLAN

Respond with:
- "OK" if no issues
- Otherwise: "RED FLAGS:" followed by bullets
EOF
)

curl -s https://api.openai.com/v1/responses \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg prompt "$PROMPT" '{
    model: "gpt-4.1-mini",
    input: $prompt
  }')" \
| jq -r '.output[0].content[0].text'| sed 's/^RED FLAGS:/\x1b[31mRED FLAGS:\x1b[0m/'

