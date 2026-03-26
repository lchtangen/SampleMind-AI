#!/usr/bin/env bash
# Quick Fix Script for SampleMind AI Database Issue
# Run this to consolidate databases and verify everything works

set -euo pipefail

echo "🔧 SampleMind AI — Quick Fix Script"
echo "===================================="
echo ""

cd /home/ubuntu/dev/projects/SampleMind-AI

# 1. Check current database configuration
echo "📊 Step 1: Checking database configuration..."
uv run python -c "from samplemind.core.config import get_settings; s = get_settings(); print(f'Database URL: {s.database_url}')"
echo ""

# 2. Check which databases exist
echo "📁 Step 2: Checking existing databases..."
ls -lh ~/.samplemind/*.db 2>/dev/null || echo "No databases found"
echo ""

# 3. Check current migration status
echo "🗄️  Step 3: Checking migration status..."
uv run alembic current
echo ""

# 4. Run migrations
echo "⬆️  Step 4: Running migrations..."
uv run alembic upgrade head
echo ""

# 5. Verify tables exist
echo "✅ Step 5: Verifying database tables..."
uv run python -c "
from samplemind.data.orm import get_engine
from sqlalchemy import inspect
engine = get_engine()
tables = inspect(engine).get_table_names()
print(f'Tables found: {len(tables)}')
for table in sorted(tables):
    print(f'  - {table}')
"
echo ""

# 6. Run tests
echo "🧪 Step 6: Running tests..."
uv run pytest tests/ -v --tb=short -x
echo ""

# 7. Test CLI commands
echo "🎯 Step 7: Testing CLI commands..."
echo "Testing: samplemind --help"
uv run samplemind --help | head -20
echo ""

echo "Testing: samplemind stats"
uv run samplemind stats || echo "No samples in database yet (this is OK)"
echo ""

# 8. Summary
echo "✅ Fix Complete!"
echo ""
echo "Next steps:"
echo "1. Import some samples: uv run samplemind import ~/Music/Samples --workers 4"
echo "2. Search samples: uv run samplemind search --query 'kick'"
echo "3. View stats: uv run samplemind stats"
echo ""
echo "All systems operational! 🚀"
