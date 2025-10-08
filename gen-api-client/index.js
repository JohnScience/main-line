import fs from "fs";
import { dirname, resolve } from "path";

import { createClient } from "@hey-api/openapi-ts";
import { SyntaxKind, Project } from "ts-morph";

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

async function genApiClient(input, output) {
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

    await createClient({
        input,
        output: genClientPath,
    });
}

function modifyFormDataBodySerializer(project, output) {
    const file = project.addSourceFileAtPath(resolve(output, "src", "gen-client", "core", "bodySerializer.gen.ts"));
    const formDataBodySerializer = file.getVariableDeclarationOrThrow("formDataBodySerializer");
    const initializer = formDataBodySerializer.getInitializerIfKindOrThrow(
        SyntaxKind.ObjectLiteralExpression
    );
    const bodySerializerProp = initializer.getPropertyOrThrow("bodySerializer");
    if (bodySerializerProp.getKind() !== SyntaxKind.PropertyAssignment) {
        throw new Error("Expected bodySerializer to be a PropertyAssignment");
    }
    const bodySerializerArrowFn = bodySerializerProp.getInitializerIfKindOrThrow(
        SyntaxKind.ArrowFunction
    );
    const typeParam = bodySerializerArrowFn.getTypeParameters()[0];
    typeParam.setConstraint("FormData | Record<string, any> | Array<Record<string, any>>");
    const bodySerializerFnBody = bodySerializerArrowFn.getBody();
    bodySerializerFnBody.insertStatements(0, "if (body instanceof FormData) { return body; }");
    file.saveSync();
}

function getFormDataRequestDecls(project, output) {
    const sdkFile = project.addSourceFileAtPath(resolve(output, "src", "gen-client", "sdk.gen.ts"));
    return sdkFile.getVariableDeclarations().filter(decl => decl.isExported)
        .filter((decl) => {
            const initializer = decl.getInitializer();
            if (!initializer) return false;
            const initializerKind = initializer.getKind();
            const isFn = [SyntaxKind.ArrowFunction, SyntaxKind.FunctionExpression].includes(initializerKind);

            const name = decl.getName();
            console.log(`Declaration check for ${name}. Is function: ${isFn}, Kind: ${SyntaxKind[initializerKind]}`);

            return isFn;
        })
        .flatMap((decl) => {
            const fn = decl.getInitializerOrThrow();
            const body = fn.getBody();
            if (!body) return [];
            console.log(`Analyzing function body for ${decl.getName()}`);
            const callExprs = body.getDescendantsOfKind(SyntaxKind.CallExpression);
            console.log(`Found ${callExprs.length} call expressions.`);
            return callExprs.map((call) => ({
                decl,
                call,
            }));
        })
        .filter(({ call }) => {
            const arg = call.getArguments()[0];
            if (!arg?.isKind(SyntaxKind.ObjectLiteralExpression)) return false;
            return arg
                .getProperties()
                .some((p) => p.isKind(SyntaxKind.SpreadAssignment)
                    && p.getExpression().getText() === "formDataBodySerializer"
                );
        })
        .map(({ decl }) => decl);
}

function getOptionsDataTypeParams(decls) {
    return decls.map((decl) => {
        const fn = decl.getInitializerOrThrow();
        const optionsArg = fn.getParameters()[0];
        if (!optionsArg)
            throw new Error(`Function ${decl.getName()} is missing the options parameter`);
        const optionsType = optionsArg.getType();
        if (!optionsType)
            throw new Error(`\`options\` parameter in function ${decl.getName()} is missing a type`);
        const typeSymbol = optionsType.getSymbol() ?? optionsType.getAliasSymbol();
        const name = typeSymbol?.getName();
        if (name !== "Options")
            throw new Error(`\`options\` parameter in function ${decl.getName()} is not of type Options<...>. Actual symbol: ${name}`);
        const aliasTypeArgs = optionsType.getAliasTypeArguments?.() ?? [];
        if (aliasTypeArgs.length === 0) {
            throw new Error(`Options type in function ${decl.getName()} is missing the data type parameter`);
        }
        const optionsDataTypeParam = aliasTypeArgs[0];
        if (!optionsDataTypeParam)
            throw new Error(`Options type in function ${decl.getName()} is missing the data type parameter`);
        // return type names
        return optionsDataTypeParam;
    });
}


function modifyOptionsDataTypeParamDecls(project, output, dataTypes) {
    const typeFile = project.addSourceFileAtPath(
        resolve(output, "src", "gen-client", "types.gen.ts")
    );

    for (const ty of dataTypes) {
        // Try to get the type name from symbol first, then fallback to text
        const typeSymbol = ty.getAliasSymbol();
        let typeName = typeSymbol?.getName();
        console.log(`Processing type with name: ${typeName}`);

        const typeAlias = typeFile.getTypeAlias(typeName);
        if (!typeAlias) {
            console.warn(`⚠️  Type alias ${typeName} not found in types.gen.ts`);
            // List available type aliases for debugging
            const availableTypes = typeFile.getTypeAliases().map(ta => ta.getName());
            console.warn(`Available type aliases: ${availableTypes.join(', ')}`);
            continue;
        } const objTypeNode = typeAlias
            .getTypeNode();
        if (!objTypeNode) {
            console.warn(`⚠️  ${typeName} is not an object type`);
            continue;
        }

        const bodyProp = objTypeNode
            .getProperties()
            .find((p) => p.getName() === "body");

        if (!bodyProp || !bodyProp.isKind(SyntaxKind.PropertySignature)) {
            console.warn(`⚠️  Type ${typeName} has no 'body' property`);
            continue;
        }

        const oldTypeText = bodyProp.getTypeNode()?.getText() ?? "";
        if (oldTypeText.includes("FormData")) {
            console.log(`✅ ${typeName}.body already includes FormData`);
            continue;
        }

        // Modify body: replace `body: X;` → `body: X | FormData;`
        bodyProp.setType(`${oldTypeText} | FormData`);
        console.log(`✅ Updated ${typeName}.body to ${oldTypeText} | FormData`);
    }

    typeFile.saveSync();
}

function modifyApiClient(output) {
    const project = new Project();
    modifyFormDataBodySerializer(project, output);
    const formDataRequestDecls = getFormDataRequestDecls(project, output);
    if (formDataRequestDecls.length === 0) {
        console.log("No FormData request functions found. No further modifications needed.");
        return;
    }
    const dataTypes = getOptionsDataTypeParams(formDataRequestDecls);
    modifyOptionsDataTypeParamDecls(project, output, dataTypes);
}

async function main() {
    const { input, output } = parseArgs();
    await genApiClient(input, output);
    modifyApiClient(output);
}

main();
