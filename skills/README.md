# Skills

Reusable skills for Celements development.

The skills in this directory are portable and installed with the npm-based
[`skills`](https://github.com/vercel-labs/skills) CLI. The CLI handles installation, updates, agent
integration, and install scope.

## Available skills

- `celements-component`: guidance for XWiki components and Spring bean wiring.
- `celements-testing`: guidance for Celements tests based on `AbstractComponentTest`.
- `celements-vue`: guidance for Vue islands in Celements legacy pages.
- `celements-struct`: guidance for structured editor fields, object lists, and tables.
- `celements-velocity`: guidance for Celements Velocity 1.7 server-side rendering and integration.
- `lambda-exception-util`: guidance for handling checked exceptions in lambdas.

## Install

Install `skills` globally:

```bash
npm install -g skills
```

Then add the skill collection:

```bash
skills add celements/synventis-tools
```

## Update

Update installed skills with:

```bash
skills update
```
