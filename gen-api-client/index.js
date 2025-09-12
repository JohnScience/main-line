
import { createClient } from '@hey-api/openapi-ts';

function parseArgs() {
    const args = process.argv.slice(2);
    let input = null;
    let output = null;
    for (let i = 0; i < args.length; i++) {
        if (args[i] === '-i' && args[i + 1]) {
            input = args[i + 1];
            i++;
        } else if (args[i] === '-o' && args[i + 1]) {
            output = args[i + 1];
            i++;
        }
    }
    if (!input || !output) {
        console.error('Usage: node index.js -i <inputFile> -o <outputFile>');
        process.exit(1);
    }
    return { input, output };
}

const { input, output } = parseArgs();

console.log(`Generating the API client from ${input} to ${output}...`);

createClient({
    input,
    output,
});
