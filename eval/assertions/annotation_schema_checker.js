
const SCHEMA_FIELDS = {
  Text: "string",
  Persona: "string",
  GoalAction: "list",
  GoalEntity: "list",
  BenefitAction: "list",
  BenefitEntity: "list",
  triggers: "nested",
  targets: "nested",
  contains: "nested",
};

let parsed;
try {
  parsed = JSON.parse(output);
} catch (e) {
  return { pass: false, score: 0, reason: "Not valid JSON: " + e.message };
}

const errors = [];

for (const [field, type] of Object.entries(SCHEMA_FIELDS)) {
  const value = parsed[field];

  if (!(field in parsed)) {
    errors.push(`Missing field: ${field}`);
    continue;
  }

  if (type === "string") {
    if (typeof value !== "string") {
      errors.push(`${field} must be a string, got ${typeof value}`);
    }
  }

  if (type === "list") {
    if (!Array.isArray(value)) {
      errors.push(`${field} must be an array`);
    } else if (!value.every(item => typeof item === "string")) {
      errors.push(`${field} must be a list of strings`);
    }
  }

  if (type === "nested") {
    if (!Array.isArray(value)) {
      errors.push(`${field} must be an array`);
    } else if (!value.every(item => Array.isArray(item) && item.length === 2)) {
      errors.push(`${field} must be a list of 2-element lists`);
    }
  }
}

if (errors.length > 0) {
  return { pass: false, score: 0, reason: errors.join("; ") };
}

return { pass: true, score: 1, reason: "Schema valid" };