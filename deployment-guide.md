# Deploying Muscle App to Railway

This guide provides step-by-step instructions for deploying the Muscle fitness tracking application to Railway.

## Prerequisites

1. A [Railway](https://railway.app/) account
2. [Git](https://git-scm.com/) installed on your local machine
3. [Railway CLI](https://docs.railway.app/develop/cli) (optional, but recommended)

## Step 1: Prepare Your Repository

1. Ensure your code is committed to a Git repository (GitHub, GitLab, etc.)
2. Make sure your repository includes:
   - Dockerfile
   - Procfile
   - railway.toml
   - requirements.txt

## Step 2: Create a New Project on Railway

1. Log in to your [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account if not already done
5. Select the repository containing your Muscle app

## Step 3: Set Up the Database

1. In your Railway project, click "New"
2. Select "Database" → "MySQL"
3. Wait for the database to be provisioned
4. Once provisioned, click on the MySQL service to view connection details
5. Copy the connection details for the next step

## Step 4: Configure Environment Variables

1. In your Railway project, select your web service
2. Go to the "Variables" tab
3. Add the following variables using the MySQL connection details:
   - `MYSQL_HOST`: The host value from your MySQL service
   - `MYSQL_USER`: The username from your MySQL service
   - `MYSQL_PASSWORD`: The password from your MySQL service
   - `MYSQL_DATABASE`: The database name from your MySQL service
   - `MYSQL_PORT`: The port from your MySQL service (usually 3306)
   - `SECRET_KEY`: A secure random string for your application
   - `PORT`: 8000 (Railway will override this with its own PORT)

## Step 5: Initialize the Database

1. In your Railway project, go to the MySQL service
2. Click on the "Connect" tab
3. Use the Railway CLI or the provided connect command to access the MySQL shell
4. Initialize your database with the schema:
   ```
   mysql -u root -p your_database < db_schema.sql
   ```
   You may need to copy the contents of db_schema.sql and execute it manually in the MySQL shell.

## Step 6: Deploy Your Application

1. Railway will automatically deploy your application when you push changes to your repository
2. You can monitor the deployment progress in the "Deployments" tab
3. Once deployed, click on the "Settings" tab to find your application URL

## Step 7: Verify the Deployment

1. Visit your application URL to ensure it's running correctly
2. Check the logs in the "Deployments" tab for any errors

## Troubleshooting

If you encounter issues:

1. **Database Connection Issues**: Double-check your environment variables
2. **Application Errors**: Check the logs in the "Deployments" tab
3. **Build Failures**: Ensure your Dockerfile and dependencies are correctly configured

## Additional Railway Features

- **Custom Domains**: In the "Settings" tab, you can set up a custom domain
- **Metrics**: Monitor your application's performance in the "Metrics" tab
- **Scaling**: Adjust your application's resources in the "Settings" tab

## Ongoing Maintenance

- Railway automatically rebuilds and deploys your application when you push changes to your repository
- You can manually trigger a deployment from the "Deployments" tab
- Monitor your application's logs and metrics regularly

---

For more detailed information, refer to the [Railway documentation](https://docs.railway.app/).
