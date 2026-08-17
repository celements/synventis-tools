# Skills

Reusable Celements development guidance, installed through the npm-based [`skills`](https://github.com/vercel-labs/skills) CLI.

## Available Skills

- `celements-component`: XWiki components, Spring beans, and migration between them.
- `celements-testing`: JUnit and EasyMock tests based on `AbstractComponentTest`.
- `celements-webapp-vue-islands`: Vue islands integrated into legacy Celements pages.
- `celements-struct`: Celements structured editor fields, layouts, object lists, and tables.
- `celements-velocity`: Apache Velocity templates and Celements integration.
- `lambda-exception-util`: Checked exceptions in Java lambdas with `LambdaExceptionUtil`.
- `synventis-vue-style`: Vue and TypeScript conventions for Synventis, Celements, and Progon projects.

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
