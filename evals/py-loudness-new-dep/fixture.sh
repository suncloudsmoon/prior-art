#!/usr/bin/env bash
set -euo pipefail
cat > requirements.txt <<'EOF'
numpy==2.1.3
scipy==1.14.1
soundfile==0.12.1
EOF
cat > audio.py <<'EOF'
def integrated_loudness(path):
    """Integrated loudness of the WAV file at `path`, in LUFS (ITU-R BS.1770)."""
    raise NotImplementedError
EOF
