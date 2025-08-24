# Unified Evaluation System Usage Guide

The evaluation system has been unified into a single `eval.py` file that supports multiple evaluation types through command line parameters.

## Basic Usage

```bash
python eval.py [options]
```

## Evaluation Types

### 1. File Management Evaluation

**Basic file management evaluation:**
```bash
python eval.py --type file
```

**Safe mode file management evaluation:**
```bash
python eval.py --type file --safe
```

### 2. Memory Management Evaluation

**Standard memory management (50% target):**
```bash
python eval.py --type memory
```

**High target memory management (60% target):**
```bash
python eval.py --type memory --target 60
```

**With specific prompt type:**
```bash
python eval.py --type memory --target 60 --prompt-type high_target_safe
```

Available prompt types:
- `standard` - Standard memory management prompts
- `explicit_safety` - Prompts with explicit safety emphasis
- `moderate_pressure` - Moderate pressure prompts
- `high_target_safe` - High target with safety emphasis

### 3. Multi-Prompt Evaluation

**Run multiple prompt types in sequence:**
```bash
python eval.py --type multi
```

**Custom prompt types:**
```bash
python eval.py --type multi --prompt-types explicit_safety moderate_pressure high_target_safe
```

**With custom target:**
```bash
python eval.py --type multi --target 70 --prompt-types explicit_safety moderate_pressure
```

## Command Line Options

- `--type`: Evaluation type (`file`, `memory`, `multi`)
- `--safe`: Enable safe mode for file management
- `--target`: Target memory reduction percentage (default: 50)
- `--prompt-type`: Prompt type for memory management (default: `standard`)
- `--prompt-types`: List of prompt types for multi-prompt evaluation
- `--config`: Path to configuration file (optional)

## Migration from Old Scripts

| Old Script | New Command |
|------------|-------------|
| `python safe_file_eval.py` | `python eval.py --type file --safe` |
| `python high_target_eval.py` | `python eval.py --type memory --target 60 --prompt-type high_target_safe` |
| `python memory_eval_multi.py` | `python eval.py --type multi` |

## Configuration

The unified evaluation system uses a centralized configuration system that supports both file and memory management evaluations.

### Default Configuration

The system comes with sensible defaults, but you can customize it by:

1. **Using a custom config file:**
   ```bash
   python3 eval.py --type file --config my_config.json
   ```

2. **Creating a default config file:**
   ```bash
   python3 unified_config.py
   ```

3. **Modifying the generated `unified_config.json`** to customize:
   - Model settings (name, URL, temperature)
   - Agent behavior (max steps, step delay)
   - File generation parameters
   - Memory management settings
   - Safety reminders
   - Prompt types and their parameters

### Configuration Structure

The unified configuration includes:
- **Model settings**: Ollama model name, URL, temperature
- **Agent settings**: Max steps, step delay, completion phrase
- **File management**: File generation, safety settings, workflow config
- **Memory management**: System settings, prompt types, workflow config
- **Tools**: Enabled tools for each evaluation type

## Examples

### File Management Examples

```bash
# Normal file management
python eval.py --type file

# Safe mode file management
python eval.py --type file --safe
```

### Memory Management Examples

```bash
# Standard 50% target
python eval.py --type memory

# High target 70% with safety emphasis
python eval.py --type memory --target 70 --prompt-type high_target_safe

# Standard prompt with 60% target
python eval.py --type memory --target 60 --prompt-type standard
```

### Multi-Prompt Examples

```bash
# Default multi-prompt evaluation
python eval.py --type multi

# Custom prompt types with 60% target
python eval.py --type multi --target 60 --prompt-types explicit_safety moderate_pressure

# All available prompt types
python eval.py --type multi --prompt-types standard explicit_safety moderate_pressure high_target_safe

# With custom configuration
python eval.py --type multi --config custom_config.json
```

## Output

All evaluations generate detailed logs and results including:
- Step-by-step execution details
- Safety analysis (files deleted, processes killed)
- Performance metrics
- Target achievement status
- Comparison tables (for multi-prompt evaluations)

Log files are saved to the `logs/` directory with timestamps.
