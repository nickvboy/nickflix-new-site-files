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
        await client.access({
            host: process.env.FTP_HOST || "f29-preview.awardspace.net",
            user: process.env.FTP_USERNAME,
            password: process.env.FTP_PASSWORD,
            port: 21,
            secure: false
        });

        console.log('Connected to FTP server');

        const buildDir = path.join(__dirname, '..', 'dist');
        const publicDir = path.join(__dirname, '..', 'public');
        
        if (!fs.existsSync(buildDir)) {
            throw new Error('Build directory not found. Please run build command first.');
        }

        // Navigate to the hostname directory
        console.log('Navigating to site directory...');
        await client.cd(process.env.FTP_SITE_DIR || 'nickflix2.atwebpages.com');

        // Clear existing files (optional)
        console.log('Clearing existing files...');
        try {
            await client.clearWorkingDir();
        } catch (err) {
            console.log('No existing files to clear or error clearing:', err.message);
        }

        // Upload the PHP files first
        console.log('Uploading PHP files...');
        await client.uploadFromDir(publicDir);

        // Upload the build directory contents
        console.log('Uploading build files...');
        await client.uploadFromDir(buildDir);
        
        console.log('Deployment completed successfully!');
    } catch (err) {
        console.error('Error during deployment:', err);
        if (err.code === 530) {
            console.log('Authentication failed. Please check your credentials.');
        } else if (err.code === 550) {
            console.log('Directory access error. Check if the directory exists in your FTP root.');
        }
    } finally {
        client.close();
    }
}

deployToFTP(); 