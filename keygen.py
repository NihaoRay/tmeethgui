from license_manager import generate_license

def main():
    print("=" * 40)
    print("  授权码生成工具（开发者专用）")
    print("=" * 40)

    while True:
        machine_code = input("\n请输入客户的机器码: ").strip()
        if not machine_code:
            break
        license_key = generate_license(machine_code)
        print(f"授权码: {license_key}")
        print("（把这个授权码发给客户即可）")

if __name__ == "__main__":
    main()