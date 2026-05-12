<p align="center">
  <a href="https://cek.neolab.finance/" target="blank"><img src="docs/assets/Context-Engineering-Kit6.png" width="512" alt="Context Engineering Kit - 上下文工程技术" /></a>
</p>

<div align="center">

[![License](https://img.shields.io/badge/license-GPL%203.0-blue.svg)](LICENSE)
[![agentskills.io](https://img.shields.io/badge/format-agentskills.io-purple.svg)](https://agentskills.io)
[![Mentioned in Awesome Claude Code](https://awesome.re/mentioned-badge.svg)](https://github.com/hesreallyhim/awesome-claude-code)

Claude Code、OpenCode、Cursor、Antigravity 等的高级上下文工程技术和模式。

[快速开始](#快速开始) · [插件](#插件列表) · [Github Action](https://cek.neolab.finance/guides/ci-integration) · [参考](https://cek.neolab.finance/reference) · [文档](https://cek.neolab.finance/)

</div>

# [Context Engineering Kit](https://cek.neolab.finance)

精心制作的高级上下文工程技术和模式集合，具有最小的 token 占用，专注于提高代理结果质量和可预测性。

该市场基于我们公司开发人员长期日常使用的提示，辅以来自基准测试论文和高质量项目的插件。

## 核心特性

- **简单易用** — 无需任何依赖即可安装和使用。包含自动使用的技能和自解释的命令。
- **Token 高效** — 精心设计的提示和架构，在可能的情况下优先使用带有子代理的命令导向技能，而不是通用信息技能，以最小化不必要的上下文信息。
- **质量导向** — 每个插件专注于在特定领域有意义地改善代理结果。
- **细粒度** — 只安装你需要的插件。每个插件只加载其特定的代理、命令和技能。没有重叠或冗余的技能。
- **科学验证** — 插件基于经过可信赖的基准测试和研究验证的技术和模式。
- **开放标准** — 技能基于 [agentskills.io](https://agentskills.io) 规范。[SDD](https://cek.neolab.finance/plugins/sdd) 插件基于 **Arc42** 软件开发文档规范标准。

## 快速开始

### 安装所有插件

```bash
npx skills add NeoLabHQ/context-engineering-kit
```

### 安装单个插件

```bash
npx skills add NeoLabHQ/context-engineering-kit/sdd
npx skills add NeoLabHQ/context-engineering-kit/reflect
npx skills add NeoLabHQ/context-engineering-kit/do-and-judge
```

## 插件列表

### 🏗️ [SDD](https://cek.neolab.finance/plugins/sdd) — 规范驱动开发

使用 Arc42 规范的软件架构和设计文档框架。

### 🔄 [Reflect](https://cek.neolab.finance/plugins/reflect) — 反思

代理结果质量和改进的自动评估。

### ⚖️ [Do and Judge](https://cek.neolab.finance/plugins/do-and-judge) — 执行与判断

执行任务并自我评估结果的质量。

### 🎯 [Meta Judge](https://cek.neolab.finance/plugins/meta-judge) — 元判断

评估代理结果的元质量。

### 📊 [Benchmark](https://cek.neolab.finance/plugins/benchmark) — 基准测试

代理性能基准测试框架。

### 🔍 [Research](https://cek.neolab.finance/plugins/research) — 研究

深度研究和信息收集。

### 💡 [Creative Sampling](https://cek.neolab.finance/plugins/creative-sampling) — 创意采样

创意和解决方案的多样化生成。

### 🛠️ [Code Quality](https://cek.neolab.finance/plugins/code-quality) — 代码质量

代码质量和最佳实践检查。

### 📝 [Git Worktrees](https://cek.neolab.finance/plugins/git-worktrees) — Git 工作树

Git 工作树管理命令。

### 🚀 [CI Integration](https://cek.neolab.finance/plugins/ci-integration) — CI 集成

GitHub Action 集成。

## 使用方法

### SDD 插件

```bash
# 创建架构文档
/sdd create

# 更新现有文档
/sdd update

# 审查文档
/sdd review
```

### Reflect 插件

```bash
# 评估代理结果
/reflect evaluate

# 改进建议
/reflect improve
```

### Do and Judge 插件

```bash
# 执行任务并自我评估
/do-and-judge "实现用户认证系统"
```

## 配置

在项目根目录创建 `.context-kit.yaml`：

```yaml
plugins:
  - sdd
  - reflect
  - do-and-judge

settings:
  quality_threshold: 8
  max_iterations: 3
```

## 开发

```bash
git clone https://github.com/NeoLabHQ/context-engineering-kit.git
cd context-engineering-kit
npm install
npm run dev
```

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

## 许可证

[GPL 3.0](LICENSE)
