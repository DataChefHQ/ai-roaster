# AI Roaster 😈

AI Roaster is an AI-powered roasting platform that generates witty and hilarious "roasts" for team members based on
their unique characteristics. This project combines a serverless backend with dynamic AI processing, voice-based
interactions, and customizable roast outputs.

## How We Roasted Our Teammates 😂

[![Watch the Video](./src/static/images/roast-video-gif.gif)](https://links.datachef.co/happy-2025-video)

## Features

- 🌶 **Funny and Personalized Roasts**: Create tailored and hilarious roasts for team members using their characteristics
  and data.
- 🔥 **Dynamic Roast Image Generation**: Generate roast-themed images unique to each team member.
- 🌐 **Web Application**: A polished web interface for users to interact with the roasting experience.
- 🔗 **Unique URLs for Roasts**: Share roasts easily using one-click URLs.
- 🎙 **Voice Output Support**: Listen to your roast via Text-to-Speech (TTS) audio.

**And it’s totally SERVERLESS! 😎**

## Tech Stack

- **Backend**: Python (Flask), AWS Lambda
- **Frontend**: HTML, CSS, JavaScript
- **Serverless Framework**: AWS infrastructure setup and deployment
- **Dependencies**:
    - Flask, Werkzeug, OpenAI API
    - Boto3 for AWS interactions

## Getting Started

### Prerequisites

1. You will need the following tools:
- Python 3.10 or later
- Node.js for Serverless Framework integration
- AWS CLI configured with the required permissions

2. **Create a Bucket to store assets**:
   - Create an S3 bucket in your AWS account to store the roast images and other assets.
   - Update the `ASSET_BUCKET` value in the `.env` file with the bucket name.

3. **Create a Deployment Role**:  
   The GitHub workflow uses [GitHub AWS OIDC](https://aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws/).
   - Create an IAM role in your AWS account for GitHub Actions.
   - Update the `GITHUB_CI_ROLE` value in the `.env` file (GitHub Actions will use this role to deploy the project).

4. **Set Up the OpenAI API Key**:
   - Generate an OpenAI API Key.
   - Store the key in AWS Secrets Manager.
   - Update the `OPENAI_KEY_SECRET_NAME` in the `.env` file with the key's secret name.

5. **Set Other Environment Variables**:
   - Update `ASSET_BUCKET`, `AWS_ACCOUNT` and `REGION` in the `.env` file.

### Training data

To bring the roasting experience to life, you need to provide descriptions and images for your teammates. Follow the 
steps below to populate the database:

1. **Create Roast Descriptions**:
   - Provide a detailed description of the person, including quirky traits, unique experiences, and anything that can
     serve as roast material—bonus points if you include pre-written roasts!
   - Save each roast in a separate `.txt` file within the `src/roasts` directory.
   - Use clear, descriptive file names (e.g., `john_doe.txt`).

2. **Add Corresponding Images**:
   - For each teammate, provide their image.
   - Save the images in the `src/static/images/team` directory.
   - Use the same naming convention as the `.txt` files (e.g., `john_doe.png` or `john_doe.jpg`).

### Running Locally

1. **Set Up the Environment**:
   ```bash
   pip install poetry
   poetry install
   ```
2. **Configure environment variables**: Ensure your `.env` file is set up correctly and has the correct values.
3. **Start the Server**:
   ```bash
   python -m src.main
   ```
4. **Open the application in your browser at**:
   ```
   http://127.0.0.1:5000/
   ```

## Deployment

The project uses the Serverless Framework for deployment on AWS Lambda, with GitHub Actions for deploying to AWS. 
To deploy:
- Commit your changes to the `master` branch.
- The GitHub Actions pipeline will deploy to AWS and host your website.

## Project Structure

```
Ai-Roaster/
├── src/
│   ├── main.py                # Flask app and API handlers
│   ├── bedrock.py             # Core AI logic for finding team members and roasting
│   ├── roasts/                # Roast content files
│   ├── static/                # Frontend assets (CSS, JS, images)
│   ├── templates/             # HTML templates for the web app
├── serverless.yml             # Serverless configuration
├── pyproject.toml             # Python dependencies (Poetry)
├── package.json               # Node.js dependencies
```

## Contributing

1. Fork the repository and create a branch for your feature.
2. Submit a pull request with detailed changes and test cases.

## License

This project is licensed under the MIT License.