import fs from "fs";
import { createClient } from "@hey-api/openapi-ts";
import { dirname, resolve } from "path";

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
        console.error('Usage: node index.js -i <inputFile> -o <outputDirectory>');
        process.exit(1);
    }
    return { input, output };
}

function copyDirRecursive(srcDir, destDir) {
    const entries = fs.readdirSync(srcDir, { withFileTypes: true });
    for (const entry of entries) {
        const srcPath = resolve(srcDir, entry.name);
        const destPath = resolve(destDir, entry.name);
        if (entry.isDirectory()) {
            if (!fs.existsSync(destPath)) {
                fs.mkdirSync(destPath, { recursive: true });
            }
            copyDirRecursive(srcPath, destPath);
        } else if (entry.isFile()) {
            const destParent = dirname(destPath);
            if (!fs.existsSync(destParent)) {
                fs.mkdirSync(destParent, { recursive: true });
            }
            fs.copyFileSync(srcPath, destPath);
        }
    }
}

function genApiClient(input, output) {
    console.log(`Generating the API client from ${input} to ${output}...`);
    const outputDirectoryExists = fs.existsSync(output);

    if (!outputDirectoryExists) {
        console.log(`Output directory ${output} does not exist. Recursively creating the directory...`);
        fs.mkdirSync(output, { recursive: true });
    }

    if (outputDirectoryExists && fs.readdirSync(output).length > 0) {
        console.error(`Output directory ${output} is not empty. Aborting to avoid overwriting existing files.`);
        process.exit(1);
    }

    copyDirRecursive(resolve(__dirname, "api-client-template"), output);

    const genClientPath = resolve(output, "src", "gen-client");

    if (!fs.existsSync(genClientPath)) {
        console.error(`Generated client path directory ${genClientPath} does not exist after copying the template. Aborting.`);
        process.exit(1);
    }

    fs.mkdirSync(genClientPath, { recursive: true });

    createClient({
        input,
        output: genClientPath,
    });
}

const { input, output } = parseArgs();
genApiClient(input, output);
