# Practical Deployment Steps for Muscle App

This document provides the exact commands and steps needed to deploy your Muscle app to Railway.

## Step 1: Prepare Your Repository

1. Initialize Git repository (if not already done)
```bash
git init
git add .
git commit -m "Prepare for deployment"
```

2. Create GitHub repository at https://github.com/new

3. Connect your local repository to GitHub
```bash
git remote add origin https://github.com/plamenyankov/muscle.git
git branch -M main
git push -u origin main
```

## Step 2: Set Up Railway Account

1. Sign up for Railway at https://railway.app/
2. Install Railway CLI
```bash
npm i -g @railway/cli
```

3. Login to Railway CLI
```bash
railway login
```

## Step 3: Create Railway Project

1. Create a new project from the Railway Dashboard
2. Link your GitHub repository

## Step 4: Set Up MySQL on Railway

1. Add MySQL service to your project
```bash
railway add
# Select MySQL when prompted
```

2. Get your database connection information
```bash
railway variables
```

## Step 5: Configure Environment Variables

1. Set up your application's environment variables:
```bash
railway variables set \
MYSQL_HOST="your-mysql-host" \
MYSQL_USER="your-mysql-user" \
MYSQL_PASSWORD="your-mysql-password" \
MYSQL_DATABASE="muscle_fitness" \
MYSQL_PORT="3306" \
SECRET_KEY="your-secret-key" \
DEBUG="False"
```

## Step 6: Initialize Database

1. Upload schema to your Railway MySQL instance:
```bash
cat db_schema.sql | railway run mysql
```

## Step 7: Deploy Your Application

1. Trigger a deployment:
```bash
railway up
```

2. Monitor the deployment status:
```bash
railway status
```

3. Open your deployed application:
```bash
railway open
```

## Step 8: Set Up CI/CD with GitHub Actions

1. Create a Railway token:
```bash
railway login --browserless
# Copy the token that is output
```

2. Add Railway token to GitHub repository secrets:
   - Go to your repository on GitHub
   - Click Settings > Secrets > New repository secret
   - Name: RAILWAY_TOKEN
   - Value: [paste your token]

3. The GitHub Actions workflow we created (.github/workflows/main.yml) will automatically deploy changes to Railway when you push to main.

## Step 9: Monitor Your Application

1. View application logs:
```bash
railway logs
```

2. Check the status of your services:
```bash
railway status
```

## Step 10: Set Up Custom Domain (Optional)

1. Purchase a domain name from a provider like Namecheap or GoDaddy

2. Configure your custom domain in Railway Dashboard:
   - Go to your service settings
   - Click on the "Domains" tab
   - Add your domain name
   - Follow the DNS configuration instructions

3. Verify your domain is correctly set up:
```bash
dig your-domain.com
```

---

Remember to replace placeholder values with your actual credentials and URLs.
