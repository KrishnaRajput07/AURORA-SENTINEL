// Test HuggingFace Inference API directly
require('dotenv').config({ path: './ai-intelligence-layer/.env' });
const axios = require('axios');
const fs = require('fs');

async function testHuggingFace() {
    const apiKey = process.env.HF_ACCESS_TOKEN;
    
    if (!apiKey) {
        console.error('❌ HF_ACCESS_TOKEN not found in .env file');
        return;
    }

    console.log('✅ HuggingFace API Key found:', apiKey.substring(0, 10) + '...');
    console.log('');

    // Test with a simple test image (1x1 pixel PNG)
    const testImageBase64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';
    const imageBuffer = Buffer.from(testImageBase64, 'base64');

    // Updated list of working models (2024)
    const models = [
        'Salesforce/blip-image-captioning-base',
        'Salesforce/blip-image-captioning-large',
        'nlpconnect/vit-gpt2-image-captioning',
        'microsoft/git-base',
        'microsoft/git-large',
        'ydshieh/vit-gpt2-coco-en'
    ];

    console.log('Testing HuggingFace models...\n');

    for (const model of models) {
        try {
            console.log(`Testing: ${model}`);
            
            const response = await axios.post(
                `https://api-inference.huggingface.co/models/${model}`,
                imageBuffer,
                {
                    headers: {
                        'Authorization': `Bearer ${apiKey}`,
                        'Content-Type': 'application/octet-stream'
                    },
                    timeout: 15000
                }
            );

            if (response.data) {
                console.log('  ✅ SUCCESS!');
                console.log('  Response:', JSON.stringify(response.data, null, 2));
                console.log('');
            }
        } catch (error) {
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                
                if (status === 503) {
                    console.log('  ⏳ Model loading (503)');
                    if (data && data.estimated_time) {
                        console.log(`  Estimated wait: ${data.estimated_time}s`);
                    }
                } else if (status === 410) {
                    console.log('  ❌ Model deprecated (410)');
                } else if (status === 429) {
                    console.log('  ⚠️ Rate limit exceeded (429)');
                } else if (status === 401) {
                    console.log('  ❌ Authentication failed (401) - Check API key');
                } else {
                    console.log(`  ❌ Error ${status}:`, data);
                }
            } else {
                console.log('  ❌ Network error:', error.message);
            }
            console.log('');
        }
    }

    console.log('\n=== Summary ===');
    console.log('If all models show 503 (loading), wait a few minutes and try again.');
    console.log('If all models show 410 (deprecated), we need to find newer models.');
    console.log('If you see 401, check your HuggingFace API token.');
}

testHuggingFace().catch(console.error);
