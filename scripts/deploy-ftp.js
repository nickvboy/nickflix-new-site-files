import { Client } from 'basic-ftp';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import dotenv from 'dotenv';
import { dirname } from 'path';

dotenv.config();

// ES modules don't have __dirname, so we need to create it
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function deployToFTP() {
    const client = new Client();
    client.ftp.verbose = true;

    try {
        console.log('Connecting to AwardSpace FTP server...');
        await client.access({
            host: process.env.FTP_HOST || "f29-preview.awardspace.net",
            user: process.env.FTP_USERNAME,
            password: process.env.FTP_PASSWORD,
            port: 21,
            secure: false
        });

        console.log('Connected to AwardSpace FTP server');

        const buildDir = path.join(__dirname, '..', 'dist');
        const publicDir = path.join(__dirname, '..', 'public');
        
        if (!fs.existsSync(buildDir)) {
            throw new Error('Build directory not found. Please run build command first.');
        }

        // Navigate to the hostname directory
        console.log('Navigating to site directory...');
        await client.cd(process.env.FTP_SITE_DIR || '');
        
        // List the current directory to verify
        console.log('Current directory contents:');
        const currentDirContents = await client.list();
        console.log(currentDirContents);

        // Clear existing files (if needed)
        console.log('Clearing existing files...');
        try {
            // Don't delete the PHP handler file
            const files = await client.list();
            for (const file of files) {
                // Skip important files like .htaccess or specific PHP files if needed
                if (file.name !== '.htaccess' && file.name !== 'index.php') {
                    if (file.isDirectory) {
                        await client.removeDir(file.name);
                    } else {
                        await client.remove(file.name);
                    }
                }
            }
        } catch (err) {
            console.log('Error clearing files:', err.message);
        }

        // Upload the public directory first (if it exists)
        if (fs.existsSync(publicDir)) {
            console.log('Uploading public files...');
            await client.uploadFromDir(publicDir);
        }

        // Upload the build directory contents
        console.log('Uploading build files...');
        await client.uploadFromDir(buildDir);
        
        // Create .htaccess for React routing (SPA)
        console.log('Creating .htaccess for React routing...');
        const htaccessContent = `
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
`;
        
        // Create temporary .htaccess file
        const tempHtaccessPath = path.join(__dirname, 'temp-htaccess');
        fs.writeFileSync(tempHtaccessPath, htaccessContent);
        await client.uploadFrom(tempHtaccessPath, '.htaccess');
        fs.unlinkSync(tempHtaccessPath);
        
        console.log('Deployment to AwardSpace completed successfully!');
    } catch (err) {
        console.error('Error during deployment:', err);
        if (err.code === 530) {
            console.log('Authentication failed. Please check your AwardSpace credentials.');
        } else if (err.code === 550) {
            console.log('Directory access error. Check if the directory exists in your AwardSpace FTP root.');
        }
    } finally {
        client.close();
    }
}

deployToFTP(); 