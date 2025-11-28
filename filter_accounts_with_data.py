import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Union


def load_loose_json(text: str) -> Union[Dict[str, Any], List[Any]]:
    """Parse JSON, cho phép dư ký tự ở cuối (ví dụ thêm '}')."""
    text = text.strip()
    while text:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Cắt bớt ký tự cuối và thử lại
            text = text[:-1].rstrip()
    raise ValueError("Không thể parse JSON trong file.")


def filter_results(data: Union[Dict[str, Any], List[Any]]) -> Dict[str, Any]:
    if isinstance(data, dict):
        meta = {
            'base_names': data.get('base_names', []),
            'total_accounts': data.get('total_accounts', 0),
            'success_count': data.get('success_count', 0),
            'fail_count': data.get('fail_count', 0),
        }
        results = data.get('results', [])
    else:
        meta = {}
        results = data

    filtered = [
        entry for entry in results
        if (entry.get('accounts') or entry.get('accounts_v2'))
    ]

    output = {'results': filtered}
    output.update({k: v for k, v in meta.items() if v})
    return output


def main():
    if len(sys.argv) < 2:
        print("Usage: python filter_accounts_with_data.py <input_json> [output_json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Không tìm thấy file: {input_path}")
        sys.exit(1)

    output_path = (
        Path(sys.argv[2]) if len(sys.argv) >= 3
        else input_path.with_name(input_path.stem + '_only_with_data.json')
    )

    text = input_path.read_text(encoding='utf-8')
    data = load_loose_json(text)
    output = filter_results(data)

    total_before = len(data.get('results', [])) if isinstance(data, dict) else len(data)
    total_after = len(output['results'])

    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"Tong truoc: {total_before}")
    print(f"Sau loc: {total_after}")
    print(f"Da luu file: {output_path}")


if __name__ == '__main__':
    main()

