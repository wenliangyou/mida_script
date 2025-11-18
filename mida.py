import os
import re
import requests
from tqdm import tqdm
from requests.exceptions import RequestException
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# 安全文件名处理函数
def safe_filename(filename):
    return re.sub(r'[\\/*?:"<>|]', "", filename).strip()

# 输入凭据
token = 'xxx.xx-xxx'
uid = 'xxx'

# 配置参数
audio_folder = 'audio'
os.makedirs(audio_folder, exist_ok=True)  # 自动创建目录

base_url = 'https://mk-gateway-pro.singworld.cn/mk-outside/api/record/getToBeFreezeList'


# 配置请求头（完整映射自 CURL 命令）
headers = {
    # ========= 基础头 ==========
    "Host": "mk-gateway-pro.singworld.cn",    # 注意：requests 会自动处理 Host，除非需要覆盖
    "Connection": "keep-alive",
    # "Content-Length": "63",   # 自动生成，无需手动设置
    
    # ========= 认证头 ==========
    "token": "kY3zkqtiSkMnp5jwlohFvV7ZRZX25141RduaSZIR9LE.A45l8y-Rqr4p4g1URO05BeHvMwTlAZkNMoT18SEU62s",
    "Authorization": "Bearer kY3zkqtiSkMnp5jwlohFvV7ZRZX25141RduaSZIR9LE.A45l8y-Rqr4p4g1URO05BeHvMwTlAZkNMoT18SEU62s",
    "user_token": "kY3zkqtiSkMnp5jwlohFvV7ZRZX25141RduaSZIR9LE.A45l8y-Rqr4p4g1URO05BeHvMwTlAZkNMoT18SEU62s",
    
    # ========= 客户端标识 ==========
    "uid": "6308538",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF WindowsWechat(0x63090c33)XWEB/11581",
    "xweb_xhr": "1",  # 微信 XWEB 标识
    
    # ========= 内容类型及安全策略 ==========
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Sec-Fetch-Site": "cross-site",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
    
    # ========= 其他重要头 ==========
    "Referer": "https://servicewechat.com/wx689a4b8fe3fccc63/216/page-frame.html",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
params = {
    "orderBy": 1,
    "overDue": 0,
    "reqUid": uid,
}

# 获取总页数
try:
    print("正在获取数据信息...")
    initial_res = requests.post(
        url=base_url,
        headers=headers,
        json={**params, "page": 1, "rows": 20},
        timeout=10,
        verify=False
    )
    # 输出res
    # print("res:", initial_res.json())
    initial_res.raise_for_status()
    total_pages = initial_res.json()['data']['pages']
    total_items = initial_res.json()['data']['total']
except (KeyError, ValueError) as e:
    print("API响应数据结构异常:", e)
    exit()
except RequestException as e:
    print("网络请求失败:", e)
    exit()

# 收集所有音频项目
all_items = []
for page in range(1, total_pages + 1):
    try:
        response = requests.post(
            base_url,
            headers=headers,
            json={**params, "page": page, "rows": 20},
            timeout=15
        )
        response.raise_for_status()
        all_items.extend(response.json()['data']['list'])
    except Exception as e:
        print(f"第 {page} 页数据获取失败: {str(e)}")
        continue

# 统一进度条下载
print(f"\n开始下载 {total_items} 个音频文件...")
with tqdm(total=len(all_items), desc="下载进度", unit="file") as pbar:
    for idx, item in enumerate(all_items, 1):
        try:
            audio_url = item['audioUrl']
            if not audio_url.startswith('http'):
                continue
                
            # 生成安全文件名
            song_name = safe_filename(item.get('songName', f"unknown_song_{idx}"))
            singer_name = safe_filename(item.get('singerName', "unknown_singer"))
            file_name = f"{song_name}—{singer_name}.aac"
            file_path = os.path.join(audio_folder, file_name)
            
            # 检查文件是否已存在，重新命名下载
            if os.path.exists(file_path):
                pbar.set_postfix_str("文件已存在，重命名下载")
                pbar.update(1)
                file_path = os.path.join(audio_folder, f"{idx}_{file_name}")
            # if os.path.exists(file_path):
            #     pbar.set_postfix_str("文件已存在，跳过")
            #     pbar.update(1)
            #     continue
                
            # 下载音频
            with requests.get(audio_url, stream=True, timeout=20) as audio_res:
                audio_res.raise_for_status()
                with open(file_path, 'wb') as f:
                    for chunk in audio_res.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
            pbar.set_postfix_str(f"{file_name[:20]}...")
            pbar.update(1)

        except Exception as e:
            pbar.set_postfix_str(f"失败: {str(e)[:20]}")
            continue

print("\n全部下载任务完成！")


