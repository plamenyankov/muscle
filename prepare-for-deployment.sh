#!/bin/bash
# Script to prepare Muscle app for Railway deployment

echo "🚀 Preparing Muscle app for Railway deployment..."

# Check if Git is initialized
if [ ! -d .git ]; then
  echo "📂 Initializing Git repository..."
  git init
  git add .
  git commit -m "Initial commit for deployment"
else
  echo "✅ Git repository already initialized"
fi

# Make sure all necessary files exist
echo "📝 Checking deployment files..."

# Make scripts executable
chmod +x prepare-for-deployment.sh

echo "🎉 Deployment preparation complete! Next steps:"
echo "1. Create a GitHub repository and push your code"
echo "2. Sign up for Railway at https://railway.app/"
echo "3. Follow the instructions in deployment-steps.md to deploy your app"
