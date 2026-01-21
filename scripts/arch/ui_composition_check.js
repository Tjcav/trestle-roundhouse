#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const ts = require("typescript");

const files = process.argv.slice(2);
const FRONTEND_ROOT = path.join("apps", "frontend", "src");
const SCREEN_DIR = path.join(FRONTEND_ROOT, "screens");

function normalizePath(value) {
  return value.replace(/\\/g, "/");
}

const RULES = {
  cardCount: "card-count",
  rawButton: "raw-button",
  rawTable: "raw-table",
  rawDiv: "raw-div",
  screenLayout: "screen-layout",
  dangerPopconfirm: "danger-popconfirm",
  dangerPrimary: "danger-primary",
  tableSize: "table-size",
  tableActionsAlign: "table-actions-align",
  activationScope: "activation-scope",
  noActionsAlert: "no-actions-alert",
  errorDominance: "error-dominance",
};

function parseAllowances(text) {
  const allows = new Set();
  const lines = text.split(/\r?\n/);
  for (const line of lines) {
    const match = line.match(/ui-check:\s*allow\s+(.+)/i);
    if (!match) continue;
    for (const part of match[1].split(/[,\s]+/)) {
      const trimmed = part.trim();
      if (trimmed) allows.add(trimmed);
    }
  }
  return allows;
}

function isScreenFile(file) {
  return normalizePath(file).includes(`${normalizePath(SCREEN_DIR)}/`);
}

function getJsxTagName(node) {
  if (ts.isJsxSelfClosingElement(node)) return node.tagName.getText();
  if (ts.isJsxOpeningElement(node)) return node.tagName.getText();
  return null;
}

function getAttribute(node, name) {
  if (!node.attributes) return null;
  for (const prop of node.attributes.properties) {
    if (ts.isJsxAttribute(prop) && prop.name.text === name) {
      return prop;
    }
  }
  return null;
}

function getAttributeStringValue(attr) {
  if (!attr || !attr.initializer) return null;
  if (ts.isStringLiteral(attr.initializer)) return attr.initializer.text;
  if (ts.isJsxExpression(attr.initializer) && attr.initializer.expression) {
    if (ts.isStringLiteral(attr.initializer.expression)) {
      return attr.initializer.expression.text;
    }
  }
  return null;
}

function getStyleObject(attr) {
  if (!attr || !attr.initializer) return null;
  if (!ts.isJsxExpression(attr.initializer)) return null;
  const expr = attr.initializer.expression;
  if (!expr || !ts.isObjectLiteralExpression(expr)) return null;
  return expr;
}

function getObjectPropertyName(prop) {
  if (!prop.name) return null;
  if (ts.isIdentifier(prop.name)) return prop.name.text;
  if (ts.isStringLiteral(prop.name)) return prop.name.text;
  return null;
}

function report(errors, file, sourceFile, node, message) {
  const pos = sourceFile.getLineAndCharacterOfPosition(node.getStart());
  errors.push(`[UI CHECK] ${file}:${pos.line + 1}:${pos.character + 1} ${message}`);
}

function checkFile(file) {
  const normalized = normalizePath(file);
  if (!normalized.startsWith(normalizePath(FRONTEND_ROOT))) return [];
  if (!file.endsWith(".tsx") && !file.endsWith(".ts")) return [];

  const text = fs.readFileSync(file, "utf8");
  const allows = parseAllowances(text);
  const sourceFile = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const errors = [];
  let cardCount = 0;
  let hasScreenLayout = false;
  let rawText = text;

  function checkTableColumns(attr, node) {
    if (!attr || !attr.initializer || !ts.isJsxExpression(attr.initializer)) return;
    const expr = attr.initializer.expression;
    if (!expr || !ts.isArrayLiteralExpression(expr)) return;
    for (const element of expr.elements) {
      if (!ts.isObjectLiteralExpression(element)) continue;
      let isActions = false;
      let hasAlign = false;
      for (const prop of element.properties) {
        if (!ts.isPropertyAssignment(prop)) continue;
        const name = getObjectPropertyName(prop);
        if (name === "title" && ts.isStringLiteral(prop.initializer) && prop.initializer.text === "Actions") {
          isActions = true;
        }
        if (name === "align" && ts.isStringLiteral(prop.initializer) && prop.initializer.text === "right") {
          hasAlign = true;
        }
      }
      if (isActions && !hasAlign && !allows.has(RULES.tableActionsAlign)) {
        report(errors, file, sourceFile, element, "Actions column must set align: \"right\".");
      }
    }
  }

  function visit(node, ancestors) {
    if (ts.isJsxElement(node)) {
      const tag = getJsxTagName(node.openingElement);
      if (tag) ancestors.push(tag);
      handleJsx(node.openingElement, ancestors);
      node.children.forEach(child => visit(child, ancestors));
      if (tag) ancestors.pop();
      return;
    }
    if (ts.isJsxSelfClosingElement(node)) {
      handleJsx(node, ancestors);
      return;
    }
    ts.forEachChild(node, child => visit(child, ancestors));
  }

  function handleJsx(node, ancestors) {
    const tag = getJsxTagName(node);
    if (!tag) return;

    if (tag === "ScreenLayout") {
      hasScreenLayout = true;
    }

    if (tag === "Card") {
      cardCount += 1;
    }

    if (tag === "Table") {
      const sizeAttr = getAttribute(node, "size");
      const sizeValue = getAttributeStringValue(sizeAttr);
      if (!sizeAttr || sizeValue !== "small") {
        if (!allows.has(RULES.tableSize)) {
          report(errors, file, sourceFile, node, "Table must declare size=\"small\".");
        }
      }
      checkTableColumns(getAttribute(node, "columns"), node);
    }

    if (tag === "Button") {
      const dangerAttr = getAttribute(node, "danger");
      if (dangerAttr && !allows.has(RULES.dangerPopconfirm)) {
        if (!ancestors.includes("Popconfirm")) {
          report(errors, file, sourceFile, node, "Danger buttons must be wrapped in Popconfirm.");
        }
      }
      if (dangerAttr && !allows.has(RULES.dangerPrimary)) {
        const typeAttr = getAttribute(node, "type");
        const typeValue = getAttributeStringValue(typeAttr);
        if (typeValue === "primary") {
          report(errors, file, sourceFile, node, "Danger buttons must not use type=\"primary\".");
        }
      }
    }

    if (tag === "div" && isScreenFile(file) && !allows.has(RULES.rawDiv)) {
      const classAttr = getAttribute(node, "className");
      const classValue = getAttributeStringValue(classAttr);
      if (classValue && classValue.includes("page")) {
        report(errors, file, sourceFile, node, "Screen layout must not use div className \"page\".");
      }
      const styleAttr = getAttribute(node, "style");
      const styleObj = getStyleObject(styleAttr);
      if (styleObj) {
        for (const prop of styleObj.properties) {
          if (!ts.isPropertyAssignment(prop)) continue;
          const name = getObjectPropertyName(prop);
          if (!name) continue;
          if (name === "display" && ts.isStringLiteral(prop.initializer)) {
            const value = prop.initializer.text;
            if (value === "flex" || value === "grid") {
              report(errors, file, sourceFile, node, "Screen layout must not use div display flex/grid.");
            }
          }
          if (name.startsWith("padding") || name.startsWith("margin")) {
            report(errors, file, sourceFile, node, "Screen layout must not use div padding/margin styles.");
          }
        }
      }
    }

    const lowerTag = tag.toLowerCase();
    if (tag === lowerTag && ["button", "table", "alert"].includes(lowerTag)) {
      const rule = lowerTag === "button" ? RULES.rawButton : RULES.rawTable;
      if (!allows.has(rule)) {
        report(errors, file, sourceFile, node, `Use Ant component instead of raw <${lowerTag}>.`);
      }
    }
  }

  visit(sourceFile, []);

  if (isScreenFile(file) && !hasScreenLayout && !allows.has(RULES.screenLayout)) {
    errors.push(`[UI CHECK] ${file}:1:1 Screens must use <ScreenLayout>.`);
  }
  if (isScreenFile(file) && cardCount > 2 && !allows.has(RULES.cardCount)) {
    errors.push(`[UI CHECK] ${file}:1:1 Screen uses ${cardCount} Cards (max 2).`);
  }
  if (normalized.endsWith("SimulatorTable.tsx") && !allows.has(RULES.activationScope)) {
    if (/selectSimulator[\s\S]*setError\s*\(/.test(rawText)) {
      errors.push(`[UI CHECK] ${file}:1:1 Activation errors must be scoped per row, not global setError.`);
    }
  }
  if (normalized.endsWith("SimulatorActions.tsx") && !allows.has(RULES.noActionsAlert)) {
    if (/<Alert\b/.test(rawText)) {
      errors.push(`[UI CHECK] ${file}:1:1 SimulatorActions must not render Alerts (use operation-scoped alerts in the screen).`);
    }
  }
  if (normalized.endsWith("SimulatorManagement.tsx") && !allows.has(RULES.errorDominance)) {
    if (/suppressActionErrors=\{[^}]*systemError[^}]*\}/.test(rawText) && !/operationError/.test(rawText)) {
      errors.push(
        `[UI CHECK] ${file}:1:1 Operation errors must suppress action errors (include operationError in suppressActionErrors).`,
      );
    }
  }

  return errors;
}

let allErrors = [];
for (const file of files) {
  allErrors = allErrors.concat(checkFile(file));
}

if (allErrors.length) {
  for (const error of allErrors) {
    console.error(error);
  }
  process.exit(1);
}
