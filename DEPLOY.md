# 部署指南 (Deployment Guide)

## 1. 服务器配置建议
- **操作系统**: **Ubuntu 20.04 LTS 或 22.04 LTS** (强烈推荐)
  - Ubuntu 是服务器领域的标准，社区支持最好，Python 环境最稳定。
- **CPU/内存**: **2核 4G** (强烈推荐)
  - **够用吗？**：如果您是调用大模型 API（如 DeepSeek、通义千问），这个配置**完全够用**，甚至绰绰有余。OpenClaw 和 A股交易 Skill 本身占用的资源很小。
  - **什么情况不够？**：只有当您想在**本地服务器上**跑大模型（Local LLM，比如自己部署一个 7B 参数的模型）时，这个配置才不够（那时需要昂贵的 GPU 服务器）。但对于 A 股分析，调用 API 是最经济高效的。

## 2. 节点选择 (关键!)
- **推荐**: 🇨🇳 **国内节点** (上海、北京、广州、成都等均可)
- **理由**:
  1. **行情数据源**: 本系统核心依赖的腾讯 (`qt.gtimg.cn`) 和新浪数据源服务器均在**国内**。国内节点访问这些接口速度是毫秒级的，极其稳定。
  2. **模型 API**: 我们推荐的 DeepSeek 或通义千问 API 都在国内，内网连接速度极快。
  3. **避坑**: **千万不要买国外节点**。国外节点访问国内的行情接口，可能会因为网络波动、防火墙（GFW）等原因导致连接超时或数据滞后。对于交易系统来说，**数据的实时性和稳定性是第一位的**。

## 3. 快速部署步骤 (Linux)

### 第一步：系统初始化 (Ubuntu)
```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 设置时区为上海 (非常重要！确保交易时间准确)
sudo timedatectl set-timezone Asia/Shanghai

# 3. 安装 Python 和 pip
sudo apt install python3 python3-pip -y
```

### 第二步：上传代码 (推荐 Git 方式)
**这是最方便的方式！** 无需复杂的 scp 命令，直接从 GitHub/Gitee 拉取代码。

假设您的代码已经托管在 Git 仓库（如果没有，请先在本地提交并推送到 GitHub/Gitee）。

在您的 **Ubuntu 服务器终端** 上执行：

```bash
# 1. 进入 OpenClaw 的 skills 目录
# 注意：OpenClaw 的默认 skills 目录通常在 ~/.openclaw/workspace/skills
cd ~/.openclaw/workspace/skills

# 2. 克隆您的代码仓库 (已替换为您提供的地址)
# 注意：我们显式将其克隆为 ashare-trader 目录，以保持一致性
git clone https://github.com/zysun202528/ast-skills.git ashare-trader

### 更新代码 (git pull 冲突解决)
如果您在服务器上修改了文件，`git pull` 可能会报错。

**简单粗暴法 (丢弃服务器上的修改，强制覆盖)**
这是最常用的方法，因为我们通常只在本地开发，服务器只负责运行。

```bash
# 1. 强制重置到远程最新版本
git fetch --all
git reset --hard origin/main

# 2. 再次拉取 (虽然 reset 已经拉取了，但这步是双保险)
git pull
```

**温柔法 (保留修改)**
```bash
git stash
git pull
git stash pop
```
```

> **提示**: 如果是私有仓库，您可能需要配置 SSH Key 或输入账号密码。

### 第三步：安装依赖
**注意**：在较新的 Ubuntu (23.04+) 上，为了保护系统环境，默认禁止直接使用 pip。

您有两种选择：

**方案 A: 强制安装到系统 (最简单，适合独占服务器)**
```bash
cd ashare-trader
pip3 install -r requirements.txt --break-system-packages
```

**方案 B: 使用虚拟环境 (最规范)**
```bash
cd ashare-trader
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活环境并安装
source venv/bin/activate
pip3 install -r requirements.txt

# 3. 注意：如果使用虚拟环境，运行 OpenClaw 时需要指定 Python 路径
# 或者在 systemd 服务文件中修改 ExecStart
```

**推荐直接使用方案 A**，因为这是一台专门跑 OpenClaw 的服务器，不会有其他 Python 冲突。

### 第四步：重启服务 (关键步骤)
**因为找不到 `openclaw.service`，您很可能是通过 Docker 运行的 OpenClaw。**

请尝试以下命令：

**方案 A：如果是 Docker 运行 (最常见)**
```bash
# 1. 查看正在运行的容器
docker ps

# 2. 如果看到名为 'openclaw' 或类似的容器，请重启它
docker restart openclaw
# 或者
docker restart openclaw-server

# 3. 查看 Docker 日志
docker logs -f openclaw --tail 100
```

**方案 B：如果是直接运行的 Python 进程**
```bash
# 1. 查找进程 ID
ps -ef | grep python | grep openclaw

# 2. 杀掉进程 (假设 PID 是 12345)
# kill -9 12345

# 3. 重新启动 (需要知道您最初是怎么启动的，通常是 startup.sh 或者 python -m ...)
# 这一步比较危险，如果您不确定启动命令，请优先尝试 Docker 方案。
```

**如何确认技能已加载？**
在日志中（`docker logs` 或终端输出），您应该能看到类似：
`[SkillManager] Loaded skill: ashare_trader`
`[SkillManager] Registered triggers: ['大盘怎么样', ...]`

如果没有看到这些日志，说明 OpenClaw 根本没有去读 `~/.openclaw/workspace/skills` 目录。
请检查 Docker 的挂载配置，确保 `-v ~/.openclaw:/root/.openclaw` 是存在的。

### 常见问题排查

#### 1. 技能没显示在列表中？
**这很正常！** "已安装技能"列表通常只显示从应用商店安装的技能。本地侧载（Sideload）的技能可能不会出现在那里，但这不影响使用。

**请直接在聊天框测试：**
发送："**今天大盘怎么样**"
如果机器人回复了行情数据，说明安装成功！

#### 2. 权限问题 (最常见原因)
您当前是在 `/root` 目录下操作。如果是 Docker 运行的 OpenClaw，容器内的非 root 用户可能**没有权限读取 `/root` 目录下的文件**。

**请执行以下命令修复权限：**
```bash
# 1. 确保所有用户都能读取技能文件
chmod -R 755 ~/.openclaw/workspace/skills/ashare-trader

# 2. (如果还在报错) 尝试给 /root 目录增加执行权限 (仅限测试环境)
# chmod +x /root
```

#### 3. 参考其他技能
如果还是不行，请看看隔壁 `weather` 技能是怎么写的，对比一下结构：
```bash
ls -R ~/.openclaw/workspace/skills/weather
cat ~/.openclaw/workspace/skills/weather/SKILL.md
```
确保我们的 `SKILL.md` 格式和它保持一致。
在腾讯云 OpenClaw 的模型选择界面，您会看到以下选项，请按需选择：

- **DeepSeek Chat** (= **DeepSeek-V3**)
  - **推荐指数**: ⭐⭐⭐⭐⭐
  - **说明**:这就是 V3 版本。速度快，逻辑好，成本低。**日常盘中分析、生成交易建议首选此模型**。

- **DeepSeek Reasoner** (= **DeepSeek-R1**)
  - **推荐指数**: ⭐⭐⭐⭐
  - **说明**: 这是推理版 (R1)。它会在回答前进行长时间的“深度思考”（会显示思维链）。适合做极其复杂的复盘分析，但速度较慢，不适合盘中实时决策。

**结论**: 请直接选择 **DeepSeek Chat**。

## 5. 飞书(Feishu) 接入常见问题
**Q: 我是管理员，为什么提交发布后找不到“审核”按钮？**
**A:** 这是一个经典误区。**开发后台**和**管理后台**是分开的。
- 您当前在的是 **开发者后台** (open.feishu.cn)，这里只负责“提交”。
- 审核操作必须去 **飞书管理后台** (www.feishu.cn/admin)。

**审核步骤**:
1. 登录 [飞书管理后台](https://www.feishu.cn/admin)。
2. 进入 **工作台 (Workplace)** -> **应用管理 (App Management)**。
3. 找到 **应用审核 (App Audit)**。
4. 在“待审核”列表中，您会看到刚才提交的 OpenClaw 机器人，点击 **通过** 即可。

**提示**: 审核通过后，状态会变为“已启用”，此时 OpenClaw 才能正常收发消息。

## 6. 首次使用配对 (Pairing)
**现象**: 机器人在飞书回复 `OpenClaw: access not configured... Pairing code: XXXXX`。
**原因**: 这是 OpenClaw 的安全机制，防止未授权人员随意调用您的机器人（毕竟调用大模型是要花钱的）。
**解决**:
1. 登录您的 **Ubuntu 服务器终端**。
2. 复制并执行机器人提示的那行命令：
   ```bash
   openclaw pairing approve feishu <您的配对码>
   
   # 例如您截图中的情况，请执行：
   # openclaw pairing approve feishu Y5FHTCHK
   ```
3. 看到终端显示 `Approved` 后，回到飞书再发一次“你好”，机器人就会正常响应了。
