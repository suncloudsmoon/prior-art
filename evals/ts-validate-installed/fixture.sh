#!/usr/bin/env bash
set -euo pipefail
cat > package.json <<'EOF'
{
  "name": "signup-api",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "zod": "^3.25.0"
  },
  "devDependencies": {
    "typescript": "^5.8.0"
  }
}
EOF
mkdir -p src
cat > src/signup.ts <<'EOF'
export type Signup = { email: string; age: number; referralCode?: string };

// Called with the parsed JSON body of POST /signup.
export function parseSignup(body: unknown): Signup {
  return body as Signup;
}
EOF
