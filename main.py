import argparse
import json
import os
import platform
import subprocess
from pathlib import Path
from colorama import init, Fore, Style

# 初始化colorama
init(autoreset=True)


def get_config_path():
    """获取配置文件路径，适配不同操作系统"""
    home_dir = Path.home()
    return home_dir / "claude_code_switch.json"


def create_config_file(config_path):
    """创建初始配置文件"""
    default_config = {
        "services": [
            {
                "alias": "default",
                "name": "Claude Official",
                "base_url": "https://api.anthropic.com",
                "api_key": "your_api_key_here"
            },
            {
                "alias": "mirror1",
                "name": "Claude Mirror 1",
                "base_url": "https://api-mirror1.example.com",
                "api_key": "your_mirror1_api_key_here"
            }
        ]
    }

    # 确保父目录存在
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入配置文件
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=4, ensure_ascii=False)

    print(f"{Fore.GREEN}已创建配置文件: {config_path}")


def load_config(config_path):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"{Fore.RED}错误: 配置文件 {config_path} 不存在")
        print(f"{Fore.YELLOW}提示: 使用 'ccs -i' 或 'ccs --init' 创建配置文件")
        return None
    except json.JSONDecodeError:
        print(f"{Fore.RED}错误: 配置文件格式不正确")
        return None


def list_services(config):
    """列出所有可用的服务"""
    if not config or 'services' not in config:
        return

    print(f"{Fore.CYAN}可用的Claude服务配置:")
    print(f"{Fore.CYAN}{'别名':<10} {'服务商':<20} {'Base URL':<30} {'API Key'}")
    print(f"{Fore.CYAN}{'-' * 70}")

    for service in config['services']:
        # 显示API Key的前6位和后4位，中间用*替代
        api_key = service.get('api_key', '')
        masked_key = api_key[:6] + '*' * (len(api_key) - 10) + api_key[-4:] if len(api_key) > 10 else api_key

        print(
            f"{Fore.GREEN if os.getenv('ANTHROPIC_AUTH_TOKEN', 'default').strip() == api_key.strip() else ''}{service.get('alias', ''):<10} {service.get('name', ''):<20} {service.get('base_url', ''):<30} {masked_key}")


def set_environment_variables(service):
    """设置环境变量，适配不同操作系统"""
    api_key = service.get('api_key', '')
    base_url = service.get('base_url', '')

    system = platform.system()

    try:
        if system == "Windows":
            # Windows无法从Python脚本中直接修改当前命令行会话的环境变量
            # 只能打印出命令供用户执行
            print(f"{Fore.GREEN}要在当前命令行会话中设置环境变量，请执行以下命令:")
            print(f"{Fore.GREEN}cmd:")
            print(f"{Fore.CYAN}set ANTHROPIC_AUTH_TOKEN={api_key} && set ANTHROPIC_API_KEY={api_key} && set ANTHROPIC_BASE_URL={base_url}")
            print(f"{Fore.GREEN}power shell:")
            print(f"{Fore.CYAN}$env:ANTHROPIC_AUTH_TOKEN=\"{api_key}\"; $env:ANTHROPIC_API_KEY=\"{api_key}\"; $env:ANTHROPIC_BASE_URL=\"{base_url}\"")
            print(f"{Fore.YELLOW}注意: 这些设置仅在当前命令行窗口有效")
            print(f"{Fore.YELLOW}如需永久设置，请使用以下命令:")
            print(f"{Fore.CYAN}setx ANTHROPIC_AUTH_TOKEN \"{api_key}\" && setx ANTHROPIC_API_KEY \"{api_key}\" && setx ANTHROPIC_BASE_URL \"{base_url}\"")
        elif system == "Darwin" or system == "Linux":  # macOS或Linux
            # 由于Python进程无法直接修改父shell的环境变量，
            # 我们需要打印出命令让用户执行
            print(f"{Fore.GREEN}要在当前shell会话中设置环境变量，请执行以下命令:")
            print(f"{Fore.CYAN}export ANTHROPIC_AUTH_TOKEN='{api_key}' && export ANTHROPIC_API_KEY='{api_key}' && export ANTHROPIC_BASE_URL='{base_url}'")
        else:
            print(f"{Fore.YELLOW}警告: 不支持的操作系统 {system}")
            print(f"{Fore.GREEN}请手动设置以下环境变量:")
            print(f"{Fore.CYAN}ANTHROPIC_AUTH_TOKEN = {api_key}")
            print(f"{Fore.CYAN}ANTHROPIC_API_KEY = {api_key}")
            print(f"{Fore.CYAN}ANTHROPIC_BASE_URL = {base_url}")

        # 显示设置的环境变量值（完整显示API Key）
        print(f"{Fore.GREEN}环境变量值:")
        print(f"{Fore.GREEN}ANTHROPIC_AUTH_TOKEN = {api_key}")
        print(f"{Fore.GREEN}ANTHROPIC_API_KEY = {api_key}")
        print(f"{Fore.GREEN}ANTHROPIC_BASE_URL = {base_url}")

        return True
    except Exception as e:
        print(f"{Fore.RED}设置环境变量时出错: {str(e)}")
        return False


def main():
    # 设置参数
    parser = argparse.ArgumentParser(description="切换Claude Code的API Key和Base URL")
    parser.add_argument("alias", nargs='?', help="服务商别名")
    parser.add_argument("-i", "--init", action="store_true", help="创建配置文件")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    args = parser.parse_args()

    config_path = get_config_path()

    # 处理初始化参数
    if args.init:
        create_config_file(config_path)
        return

    # 加载配置
    config = load_config(config_path)
    if not config:
        return

    # 不带参数时，列出所有服务
    if args.alias is None:
        list_services(config)
        return

    # 根据别名查找服务
    service = None
    for s in config.get('services', []):
        if s.get('alias') == args.alias:
            service = s
            break

    if service:
        print(f"{Fore.CYAN}切换到服务: {service.get('name', '')}")
        set_environment_variables(service)
    else:
        print(f"{Fore.RED}错误: 未找到别名为 '{args.alias}' 的服务")
        print(f"{Fore.YELLOW}可用的服务别名:")
        for s in config.get('services', []):
            print(f"  - {s.get('alias', '')}")


if __name__ == "__main__":
    main()
