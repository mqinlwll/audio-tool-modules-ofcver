import json
from pathlib import Path

def format_analysis_result(result: dict) -> str:
    """Format a single analysis result for display."""
    if "error" in result:
        return f"Analyzing: {result['file_path']}\n  [ERROR] Failed to analyze: {result['error']}\n\n"

    channel_info = "Mono" if result["channels"] == 1 else "Stereo" if result["channels"] == 2 else f"{result['channels']} channels" if result["channels"] != "N/A" else "N/A"
    
    analysis_text = f"Analyzing: {result['file_path']}\n"
    analysis_text += f"  Bitrate: {result['bit_rate']} bps\n" if result['bit_rate'] != "N/A" else "  Bitrate: N/A\n"
    analysis_text += f"  Sample Rate: {result['sample_rate']} Hz\n" if result['sample_rate'] != "N/A" else "  Sample Rate: N/A\n"
    analysis_text += f"  Bit Depth: {result['bit_depth']} bits\n" if result['bit_depth'] != "N/A" else "  Bit Depth: N/A\n"
    analysis_text += f"  Channels: {channel_info}\n"
    analysis_text += f"  Codec: {result['codec']}\n"
    analysis_text += f"  Duration: {result['duration']} seconds\n" if result['duration'] != "N/A" else "  Duration: N/A\n"
    analysis_text += f"  Size: {result['size']} bytes\n" if result['size'] != "N/A" else "  Size: N/A\n"

    warnings = json.loads(result['warnings']) if isinstance(result['warnings'], str) else result.get('warnings', [])
    for warning in warnings:
        analysis_text += f"  [{warning.startswith('WARNING') and 'WARNING' or 'INFO'}] {warning}\n"

    analysis_text += "\n"
    return analysis_text

def write_results_to_file(results: list, output_file: Path):
    """Write analysis results to a file."""
    with open(output_file, "w") as f:
        for result in results:
            f.write(format_analysis_result(result))
    print(f"Analysis complete. Results saved to '{output_file}'")

def print_results(results: list):
    """Print analysis results to console."""
    for result in results:
        print(format_analysis_result(result)) 