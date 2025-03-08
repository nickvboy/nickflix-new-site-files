# Nickflix 2 - Movie Showcase Website

A modern movie showcase website built with React, TypeScript, and Tailwind CSS.

## Features

- Movie browsing and searching
- Coming soon section
- User profile management
- Responsive design for all devices

## Local Development

1. Clone the repository
2. Install dependencies:
   ```
   npm install
   ```
3. Create a `.env` file based on `.env.example`
4. Start the development server:
   ```
   npm run dev
   ```

## Deployment to AwardSpace for Nickflix 2

### Prerequisites

1. An AwardSpace hosting account
2. FTP credentials for your AwardSpace account

### Setup

1. Configure your `.env` file with your AwardSpace credentials:

```
FTP_HOST=f29-preview.awardspace.net
FTP_USERNAME=your_awardspace_username
FTP_PASSWORD=your_awardspace_password
FTP_SITE_DIR=nickflix2.atwebpages.com
```

2. Deploy the site to AwardSpace:

```
npm run deploy:nickflix2
```

This will:
- Build the project
- Connect to AwardSpace FTP server
- Upload the built files to your Nickflix 2 hosting account
- Create a proper .htaccess file for SPA routing

### Troubleshooting

- If you encounter "530 Login authentication failed" error, check your FTP credentials
- If you get "550 Failed to change directory" error, make sure the FTP_SITE_DIR exists and is set to `nickflix2.atwebpages.com`
- For other issues, check the verbose FTP logs in the console output

## Technologies Used

- React
- TypeScript
- Tailwind CSS
- Radix UI
- React Router
- Vite 