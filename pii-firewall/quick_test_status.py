"""
Quick test runner - Muestra estado actual de los tests.

Uso:
    python quick_test_status.py
"""

import subprocess
import sys

def run_command(cmd):
    """Ejecuta comando y retorna resultado."""
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr

def main():
    print("=" * 80)
    print("ESTADO DE TESTS - Privacy Firewall")
    print("=" * 80)
    print()
    
    # Run tests with summary
    print("Ejecutando tests...")
    returncode, stdout, stderr = run_command(
        "python -m pytest tests_integration/ -v --tb=no -q"
    )
    
    # Parse results
    lines = stdout.split('\n')
    
    # Find summary line
    for line in lines:
        if 'passed' in line or 'failed' in line:
            print("\n" + "=" * 80)
            print("RESUMEN")
            print("=" * 80)
            print(line)
            print()
    
    # Show failed tests
    print("\n" + "=" * 80)
    print("TESTS QUE FALLAN")
    print("=" * 80)
    
    failed_tests = []
    in_failed_section = False
    
    for line in lines:
        if 'FAILED' in line and '::' in line:
            # Extract test name
            parts = line.split('::')
            if len(parts) >= 2:
                test_file = parts[0].replace('tests_integration\\', '').replace('tests_integration/', '')
                test_name = '::'.join(parts[1:]).split(' ')[0]
                failed_tests.append(f"  - {test_file}::{test_name}")
    
    if failed_tests:
        for test in failed_tests:
            print(test)
    else:
        print("  ✅ ¡Todos los tests pasan!")
    
    print()
    print("=" * 80)
    print("ANÁLISIS")
    print("=" * 80)
    
    # Count by category
    phone_fails = len([t for t in failed_tests if 'phone' in t.lower()])
    dni_fails = len([t for t in failed_tests if 'dni' in t.lower()])
    date_fails = len([t for t in failed_tests if 'date' in t.lower()])
    
    if phone_fails > 0:
        print(f"  ❌ {phone_fails} tests de PHONE fallan (falta Spanish Phone Recognizer)")
    
    if dni_fails > 0:
        print(f"  ❌ {dni_fails} tests de DNI fallan (falta Spanish DNI Recognizer)")
    
    if date_fails > 0:
        print(f"  ❌ {date_fails} tests de DATE fallan (falta Spanish Date Recognizer)")
    
    if len(failed_tests) == 0:
        print("  ✅ Sistema funcionando perfectamente!")
    
    print()
    print("Ver detalles en: tests_integration/FAILING_TESTS_REPORT.md")
    print("=" * 80)
    
    return returncode

if __name__ == "__main__":
    sys.exit(main())
