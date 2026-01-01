import streamlit as st
import pandas as pd
import itertools
from collections import defaultdict
from datetime import timedelta, date
import textwrap

# ================= 0. 基础配置 =================
st.set_page_config(page_title="球蟒繁育系统 Ultimate", layout="wide")

st.markdown(textwrap.dedent("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stDataFrame { font-size: 14px; }
    a { text-decoration: none; font-weight: bold; color: #60a5fa; }
    
    /* 风险提示 - 专业深红风格 */
    .risk-alert { 
        padding: 10px; 
        background-color: #450a0a; 
        color: #fca5a5; 
        border-radius: 4px; 
        border-left: 4px solid #ef4444;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 500;
    }
    
    /* 统计卡片 - 数据终端风格 */
    div[data-testid="stMetric"] {
        background-color: #1e293b;
        padding: 15px;
        border-radius: 6px;
        border: 1px solid #334155;
    }

    /* 侧边栏卡片 */
    .dev-card { background-color: #262730; border: 1px solid #3f3f46; border-radius: 8px; padding: 15px; margin-top: 20px; font-size: 13px; color: #e4e4e7; }
    .dev-title { font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #fff; }
    .dev-desc { color: #a1a1aa; margin-bottom: 12px; line-height: 1.4; font-size: 12px; }
    .contact-row { display: flex; align-items: center; margin-bottom: 8px; }
    .wechat-dot { height: 8px; width: 8px; background-color: #4ade80; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .tg-plane { display: inline-block; margin-right: 8px; width: 8px; text-align: center; font-size: 12px; line-height: 1; }
    .highlight-green { color: #4ade80; font-weight: 500; }
    .highlight-blue { color: #38bdf8; font-weight: 500; }
    .signature { margin-top: 15px; padding-top: 10px; border-top: 1px dashed #3f3f46; font-size: 12px; color: #a1a1aa; text-align: center; font-style: italic; font-family: monospace; }
    .copyright { text-align: center; margin-top: 5px; font-size: 10px; color: #52525b; }
</style>
"""), unsafe_allow_html=True)

# ================= 1. 核心数据库 =================
GENE_DB = {
    # --- 1. 显性/不完全显性 ---
    # [BEL Complex]
    "Mojave": {"cn": "莫哈维", "type": "显性", "group": "BEL"},
    "Lesser": {"cn": "白金", "type": "显性", "group": "BEL"},
    "Butter": {"cn": "黄油", "type": "显性", "group": "BEL"},
    "Bamboo": {"cn": "竹子", "type": "显性", "group": "BEL"},
    "Russo": {"cn": "卢瑟", "type": "显性", "group": "BEL"},
    "Phantom": {"cn": "幻影", "type": "显性", "group": "BEL"},
    "Mystic": {"cn": "神秘", "type": "显性", "group": "BEL"},
    "Special": {"cn": "特别", "type": "显性", "group": "BEL"},
    "Mocha": {"cn": "摩卡", "type": "显性", "group": "BEL"},

    # [ALS Complex]
    "Black Pastel": {"cn": "黑蜡笔", "type": "显性", "group": "ALS"},
    "Cinnamon": {"cn": "肉桂", "type": "显性", "group": "ALS"},
    "Het Red Axanthic": {"cn": "HRA (红缺黄)", "type": "显性", "group": "ALS"},

    # [Yellow Belly Complex]
    "Yellow Belly": {"cn": "黄腹", "type": "显性", "group": "YB"},
    "Asphalt": {"cn": "沥青", "type": "显性", "group": "YB"},
    "Gravel": {"cn": "碎石", "type": "显性", "group": "YB"},
    "Spark": {"cn": "火花", "type": "显性", "group": "YB"},
    "Specter": {"cn": "幽灵(Specter)", "type": "显性", "group": "YB"},

    # [Spider Complex]
    "Spider": {"cn": "蜘蛛", "type": "显性", "group": "Spider"},
    "Spotnose": {"cn": "斑鼻", "type": "显性", "group": "Spider"},
    "Woma": {"cn": "沃玛", "type": "显性", "group": "Spider"},
    "Hidden Gene Woma": {"cn": "HGW (隐沃玛)", "type": "显性", "group": "Spider"},
    "Champagne": {"cn": "香槟", "type": "显性", "group": "Spider"},

    # [Acid Complex]
    "Acid": {"cn": "酸 (Acid)", "type": "显性", "group": "Acid"},
    "Confusion": {"cn": "困惑 (Confusion)", "type": "显性", "group": "Acid"},

    # [High-End / Hype]
    "Stranger": {"cn": "陌客 (Stranger)", "type": "显性"},
    "Mahogany": {"cn": "红木", "type": "显性"},
    "Red Stripe": {"cn": "红条", "type": "显性"},
    "Bongo": {"cn": "邦戈 (Bongo)", "type": "显性"},
    "Cypress": {"cn": "柏树", "type": "显性"},
    "Leopard": {"cn": "豹纹", "type": "显性"},
    "Blackhead": {"cn": "黑头", "type": "显性"},
    "Enchi": {"cn": "安奇", "type": "显性"},
    "Orange Dream": {"cn": "橙梦 (OD)", "type": "显性"},
    "Fire": {"cn": "火", "type": "显性"},
    "Vanilla": {"cn": "香草", "type": "显性"},
    "Disco": {"cn": "迪斯科", "type": "显性"},
    "Thunder": {"cn": "雷电", "type": "显性"},
    "Banana": {"cn": "香蕉", "type": "显性"},
    "Pastel": {"cn": "蜡笔", "type": "显性"},
    "Pinstripe": {"cn": "细纹", "type": "显性"},
    "GHI": {"cn": "GHI", "type": "显性"},
    "Blade": {"cn": "刀锋", "type": "显性"},

    # --- 2. 隐性 ---
    "Clown": {"cn": "小丑", "type": "隐性"},
    "Pied": {"cn": "派 (Piebald)", "type": "隐性"},
    "Desert Ghost": {"cn": "沙幽 (DG)", "type": "隐性"},
    "Sunset": {"cn": "日落 (Sunset)", "type": "隐性"},
    "Monsoon": {"cn": "季风 (Monsoon)", "type": "隐性"},
    "Puzzle": {"cn": "拼图 (Puzzle)", "type": "隐性"},
    "Tri-Stripe": {"cn": "三条纹", "type": "隐性"},
    "Ultramel": {"cn": "超焦 (Ultramel)", "type": "隐性"},
    "Lavender Albino": {"cn": "薰衣草白化", "type": "隐性"},
    "Albino": {"cn": "白化", "type": "隐性"},
    "Axanthic (VPI)": {"cn": "缺黄 (VPI)", "type": "隐性"},
    "Axanthic (TSK)": {"cn": "缺黄 (TSK)", "type": "隐性"},
    "Ghost": {"cn": "幽灵/衰退 (Hypo)", "type": "隐性"},
    "Genetic Stripe": {"cn": "遗传直线", "type": "隐性"},
    "Toy": {"cn": "玩具 (Toy)", "type": "隐性"},
}

# 映射表
NAME_TO_ID_MAP = {}
for k, v in GENE_DB.items():
    display_name = f"{k} ({v['cn']})"
    NAME_TO_ID_MAP[display_name] = k

RISK_DB = {
    "Black Pastel": {2: "风险提示: Super Black Pastel 极易出现脊柱弯曲 (Kinking) 和鸭嘴畸形。"},
    "Cinnamon": {2: "风险提示: Super Cinnamon 极易出现脊柱弯曲 (Kinking) 和鸭嘴畸形。"},
    "Spider": {1: "注意: 蜘蛛基因携带神经系统问题 (Wobble)。", 2: "致死风险: Super Spider 为致死基因。"},
    "Woma": {1: "注意: 沃玛基因可能携带神经问题 (Wobble)。", 2: "致死风险: Super Woma 通常无法存活。"},
    "Hidden Gene Woma": {1: "注意: HGW 基因可能携带神经问题。", 2: "致死风险: Super HGW 为致死基因。"},
    "Champagne": {2: "致死风险: Super Champagne 为致死基因。"},
    "Spotnose": {2: "风险: Super Spotnose (Powerball) 可能伴随严重神经问题。"},
    "GHI": {2: "风险: Super GHI 生长缓慢且可能存在致死风险。"},
}

OPT_WILD = "无"
OPT_HET = "单显/杂合 (Het)"
OPT_SUPER = "超级/纯合 (Super/Visual)"
STATUS_MAP = {OPT_WILD: 0, OPT_HET: 1, OPT_SUPER: 2}

# ================= 2. 核心算法 =================

def check_genetic_risks(df, active_gene_ids):
    warnings = set()
    for idx, row in df.iterrows():
        if row['概率'] <= 0: continue
        geno_dict = dict(row['_geno_dict'])
        for gid in active_gene_ids:
            score = geno_dict.get(gid, 0)
            if gid in RISK_DB and score in RISK_DB[gid]:
                warnings.add(RISK_DB[gid][score])
    return list(warnings)

def apply_combo_rules(active_genes_dict):
    bel_count = 0
    for gid, score in active_genes_dict.items():
        if score > 0 and GENE_DB.get(gid, {}).get("group") == "BEL":
            bel_count += score
    if bel_count >= 2: return "BEL (蓝眼白路复合组)"
    
    yb_count = 0
    for gid, score in active_genes_dict.items():
        if score > 0 and GENE_DB.get(gid, {}).get("group") == "YB":
            yb_count += score
    if yb_count >= 2: return "Ivory/Highway (黄腹复合组超级体)"
    
    als_count = 0
    for gid, score in active_genes_dict.items():
        if score > 0 and GENE_DB.get(gid, {}).get("group") == "ALS":
            als_count += score
    if als_count >= 2: return "8-Ball Complex (ALS超级体 - 高风险)"
    return None

# --- 核心修改：生成更智能的 MorphMarket 链接 ---
def generate_mm_link(active_genes_dict):
    search_terms = []
    for gid, score in active_genes_dict.items():
        if score == 0: continue
        
        # 获取基因类型 (显性/隐性)
        gene_info = GENE_DB.get(gid, {})
        g_type = gene_info.get("type", "显性")
        
        term = gid
        # 显性处理
        if "显性" in g_type:
            if score == 2:
                # 显性纯合 -> Super Gene
                term = f"Super {gid}"
            else:
                # 显性杂合 -> Gene
                term = gid
        # 隐性处理
        elif "隐性" in g_type:
            if score == 1:
                # 隐性杂合 -> Het Gene
                term = f"Het {gid}"
            else:
                # 隐性纯合 -> Gene (Visual)
                term = gid
        
        search_terms.append(term)

    if not search_terms:
        # 原色
        return "https://www.morphmarket.com/us/c/reptiles/pythons/ball-pythons?trait_form=Normal"
    
    # 使用 'q' 参数进行关键词搜索，比 'genes' 参数更智能，能识别 "Super", "Het" 等修饰词
    query_str = "+".join(search_terms)
    return f"https://www.morphmarket.com/us/c/reptiles/pythons/ball-pythons?q={query_str}"

def get_gametes(genotype_dict):
    gene_options = []
    gene_ids = sorted(genotype_dict.keys())
    for gene in gene_ids:
        score = genotype_dict[gene]
        if score == 2: options = [1]
        elif score == 1: options = [0, 1]
        else: options = [0]
        gene_options.append([(gene, val) for val in options])
    return list(itertools.product(*gene_options))

def calculate_offspring(parent_a_geno, parent_b_geno):
    gametes_a = get_gametes(parent_a_geno)
    gametes_b = get_gametes(parent_b_geno)
    total = len(gametes_a) * len(gametes_b)
    outcome_counts = defaultdict(int)
    for g_a in gametes_a:
        for g_b in gametes_b:
            child_temp = defaultdict(int)
            for gene, val in g_a: child_temp[gene] += val
            for gene, val in g_b: child_temp[gene] += val
            outcome_counts[tuple(sorted(child_temp.items()))] += 1
    results = []
    for genotype_tuple, count in outcome_counts.items():
        row = dict(genotype_tuple)
        row['概率'] = (count / total) * 100
        row['_geno_dict'] = genotype_tuple
        
        # 基因计数
        gene_count = sum(1 for gene, val in genotype_tuple if val > 0)
        row['_gene_count'] = gene_count
        
        results.append(row)
    return pd.DataFrame(results).sort_values(['概率', '_gene_count'], ascending=[False, False]).reset_index(drop=True)

def format_label_with_combo(row, active_gene_ids, simplified=False):
    geno_dict = dict(row['_geno_dict'])
    combo_name = apply_combo_rules(geno_dict)
    
    if simplified:
        if combo_name: return f"{combo_name} (All Variants)"
    
    parts = []
    for gene_id in active_gene_ids:
        val = geno_dict.get(gene_id, 0)
        if val == 0: continue
        
        gene_info = GENE_DB.get(gene_id, {"type": "隐性"})
        prefix = ""
        suffix = ""
        
        if "隐性" in gene_info["type"]:
            if val == 2: suffix = "(Visual)" 
            else: suffix = "(Het)"
        else: # 显性
            if val == 2: prefix = "[Super]"
            
        label = f"{prefix} {gene_id} {suffix}"
        parts.append(label.strip())
        
    base_label = " + ".join(parts) if parts else "Wild Type (原色)"
    
    if combo_name: 
        return f"{combo_name} >>> {base_label}"
    return base_label

# ================= 3. 界面布局 =================

st.title("球蟒繁育系统 Ultimate")

# --- 侧边栏 ---
with st.sidebar:
    st.header("生产排期") 
    st.caption("输入锁配日期，推算回款周期")
    pair_date = st.date_input("最后锁配日期", date.today())
    
    d_ovulation = pair_date + timedelta(days=30)
    d_lay = d_ovulation + timedelta(days=40)
    d_hatch = d_lay + timedelta(days=58)
    d_sale = d_hatch + timedelta(days=30)
    
    st.markdown("---")
    st.markdown(f"**排卵**: {d_ovulation.strftime('%m-%d')}")
    st.markdown(f"**产蛋**: {d_lay.strftime('%m-%d')}")
    st.markdown(f"**出壳**: `{d_hatch.strftime('%Y-%m-%d')}`")
    st.success(f"上市: {d_sale.strftime('%Y-%m-%d')}")
    st.caption("*仅供参考，受温度/个体影响较大")

    # --- 左下角：开发者信息 (紧凑版，防止缩进问题) ---
    st.markdown("""
<style>
.dev-card { background-color: #262730; border: 1px solid #3f3f46; border-radius: 8px; padding: 15px; margin-top: 20px; font-size: 13px; color: #e4e4e7; }
.dev-title { font-weight: bold; font-size: 14px; margin-bottom: 8px; color: #fff; }
.dev-desc { color: #a1a1aa; margin-bottom: 12px; line-height: 1.4; font-size: 12px; }
.contact-row { display: flex; align-items: center; margin-bottom: 8px; }
.wechat-dot { height: 8px; width: 8px; background-color: #4ade80; border-radius: 50%; display: inline-block; margin-right: 8px; }
.tg-plane { display: inline-block; margin-right: 8px; width: 8px; text-align: center; font-size: 12px; line-height: 1; }
.highlight-green { color: #4ade80; font-weight: 500; }
.highlight-blue { color: #38bdf8; font-weight: 500; }
.signature { margin-top: 15px; padding-top: 10px; border-top: 1px dashed #3f3f46; font-size: 12px; color: #a1a1aa; text-align: center; font-style: italic; font-family: monospace; }
.copyright { text-align: center; margin-top: 5px; font-size: 10px; color: #52525b; }
</style>
<div class="dev-card">
<div class="dev-title">关于开发者</div>
<div class="dev-desc">Project Ball_Python_Calc 由爬宠爱好者独立开发。<br>如有新功能建议、Bug反馈，或繁育交流，欢迎联系：</div>
<div class="contact-row"><span class="wechat-dot"></span><span>WeChat: <span class="highlight-green">buckethead1</span></span></div>
<div class="contact-row"><span class="tg-plane">✈️</span><span>Telegram: <a href="https://t.me/reop2025" class="highlight-blue">@reop2025</a></span></div>
<div class="signature">"Life is short, use Python."</div>
</div>
<div class="copyright">© 2025 Project Ball_Python_Calc. All Rights Reserved.</div>
""", unsafe_allow_html=True)


# --- 1. 繁殖组设定 ---
st.markdown("#### 1. 繁殖组设定")

all_display_names = list(NAME_TO_ID_MAP.keys())
default_names = []
for k in ["Stranger", "Clown"]:
    if k in GENE_DB: default_names.append(f"{k} ({GENE_DB[k]['cn']})")

selected_display_names = st.multiselect(
    "添加基因池:", 
    options=all_display_names, 
    default=default_names, 
    label_visibility="collapsed"
)
if not selected_display_names: st.stop()

selected_gene_ids = [NAME_TO_ID_MAP[name] for name in selected_display_names]

table_data = []
for gid in selected_gene_ids:
    group_tag = f" [{GENE_DB[gid]['group']}]" if 'group' in GENE_DB[gid] else ""
    table_data.append({"Gene": gid, "中文名": GENE_DB[gid]["cn"] + group_tag, "公蛇": OPT_WILD, "母蛇 A": OPT_WILD, "母蛇 B": OPT_WILD, "母蛇 C": OPT_WILD})

df_input_source = pd.DataFrame(table_data).set_index("Gene")
col_conf = st.column_config.SelectboxColumn(options=[OPT_WILD, OPT_HET, OPT_SUPER], width="small", required=True)

edited_df = st.data_editor(df_input_source, column_config={"中文名": st.column_config.TextColumn(disabled=True), "公蛇": col_conf, "母蛇 A": col_conf, "母蛇 B": col_conf, "母蛇 C": col_conf}, use_container_width=True)

male_geno = {gid: STATUS_MAP[edited_df.loc[gid, "公蛇"]] for gid in selected_gene_ids}
females_geno = {k: {gid: STATUS_MAP[edited_df.loc[gid, f"母蛇 {k}"]] for gid in selected_gene_ids} for k in ["A", "B", "C"]}

# --- 2. 核心分析区 ---
st.divider()
st.markdown("#### 2. 遗传计算结果")

female_names = {"A": "母蛇 A", "B": "母蛇 B", "C": "母蛇 C"}
tabs = st.tabs([f"{female_names['A']}", f"{female_names['B']}", f"{female_names['C']}"])
f1_dfs = {}

for i, key in enumerate(["A", "B", "C"]):
    with tabs[i]:
        # 1. 计算
        df = calculate_offspring(male_geno, females_geno[key])
        f1_dfs[key] = df 
        
        # 2. 风控
        risks = check_genetic_risks(df, selected_gene_ids)
        if risks:
            for r in risks: st.markdown(f"<div class='risk-alert'>{r}</div>", unsafe_allow_html=True)
            
        if not df.empty:
            # 3. 基础列生成
            df['链接'] = df.apply(lambda row: generate_mm_link(dict(row['_geno_dict'])), axis=1)
            df['表现型_Full'] = df.apply(lambda row: format_label_with_combo(row, selected_gene_ids, simplified=False), axis=1)
            df['表现型_Group'] = df.apply(lambda row: format_label_with_combo(row, selected_gene_ids, simplified=True), axis=1)
            
            # ================= 统计区域 =================
            c_stat_title, c_stat_sel = st.columns([0.5, 0.5])
            with c_stat_title:
                st.markdown("##### 核心概率统计")
            with c_stat_sel:
                target_combo = st.multiselect(
                    "设定目标组合 (支持多选):", 
                    options=selected_gene_ids,
                    default=[], 
                    key=f"kpi_combo_{key}",
                    placeholder="例如: Stranger + Clown (用于智能分层筛选)"
                )

            kpi_c1, kpi_c2, kpi_c3 = st.columns(3)
            
            help_hit = "指完美遗传了您选定的所有目标基因，且均为成体/超级体表现 (Visual/Super)。"
            help_proj = "指携带了您选定的目标基因 (可能含 Het)，适合留种作为下一代繁育种源。"
            help_jackpot = "指这一窝中所有能直观看出基因变异个体 (显性超级体 + 隐性成体) 的总概率。"
            
            if not target_combo:
                # 默认显示
                prob_super = df[
                    (df['表现型_Full'].str.contains("BEL")) | 
                    (df['表现型_Full'].str.contains("Super")) |
                    (df['表现型_Full'].str.contains("Visual")) 
                ]['概率'].sum()
                kpi_c1.metric("任意极品/超级体", f"{prob_super:.1f}%", help=help_hit)
                kpi_c2.metric("请选择目标组合 ↗", "--", help="在右上方选择目标基因组合后，此处将显示该组合的特定概率。")
            else:
                # 组合计算
                def check_combo_hit(row_geno, targets, mode="strict"):
                    for t in targets:
                        val = row_geno.get(t, 0)
                        if val == 0: return False
                        g_type = GENE_DB.get(t, {}).get("type", "显性")
                        if mode == "strict":
                            # 严格模式：隐性必须2，显性必须>=1 (含2)
                            if "隐性" in g_type and val < 2: return False
                    return True

                prob_hit = df[df['_geno_dict'].apply(lambda g: check_combo_hit(dict(g), target_combo, "strict"))]['概率'].sum()
                prob_proj = df[df['_geno_dict'].apply(lambda g: check_combo_hit(dict(g), target_combo, "loose"))]['概率'].sum()
                
                combo_name = " + ".join(target_combo)
                if len(combo_name) > 15: combo_name = "目标组合" 

                kpi_c1.metric(f"完美成体 ({combo_name})", f"{prob_hit:.1f}%", help=help_hit)
                kpi_c2.metric(f"项目个体 (含 Het)", f"{prob_proj:.1f}%", help=help_proj)

            prob_jackpot = df[
                (df['表现型_Full'].str.contains("BEL")) | 
                (df['表现型_Full'].str.contains("Super")) | 
                (df['表现型_Full'].str.contains("Visual")) 
            ]['概率'].sum()
            kpi_c3.metric("超级/成体综合概率 (Total Super/Visual)", f"{prob_jackpot:.1f}%", help=help_jackpot)
            
            st.markdown("---")
            
            # ================= 列表展示 (智能分层 Smart Tiering) =================
            
            common_config = {
                "概率": st.column_config.NumberColumn(format="%.1f%%", width="small"),
                "表现型": st.column_config.Column("基因表现型 (Visual/Super 为成体/超级体)", width="large"),
                "链接": st.column_config.LinkColumn("图鉴", display_text="MorphMarket", width="small"),
                "_gene_count": None # 隐藏辅助列
            }
            
            # 如果没有选目标，就直接显示大列表
            if not target_combo:
                st.dataframe(df[['表现型_Full', '概率', '链接', '_gene_count']].rename(columns={'表现型_Full': '表现型'}), 
                             column_config=common_config, use_container_width=True, hide_index=True)
            else:
                # 选了目标，进行三层分级
                
                # 1. 完美组 (Strict Hit)
                df_tier1 = df[df['_geno_dict'].apply(lambda g: check_combo_hit(dict(g), target_combo, "strict"))]
                # 2. 项目组 (Loose Hit but not Strict)
                df_tier2 = df[
                    (df['_geno_dict'].apply(lambda g: check_combo_hit(dict(g), target_combo, "loose"))) & 
                    (~df.index.isin(df_tier1.index))
                ]
                # 3. 其他组
                df_tier3 = df[~df.index.isin(df_tier1.index) & ~df.index.isin(df_tier2.index)]
                
                # 渲染 Tier 1
                if not df_tier1.empty:
                    with st.expander(f"🎯 完美目标组 (Perfect Hits) - {len(df_tier1)} 种结果", expanded=True):
                        st.dataframe(df_tier1[['表现型_Full', '概率', '链接', '_gene_count']].rename(columns={'表现型_Full': '表现型'}),
                                     column_config=common_config, use_container_width=True, hide_index=True)
                
                # 渲染 Tier 2
                if not df_tier2.empty:
                    with st.expander(f"🧬 核心项目组 (Project Makers) - {len(df_tier2)} 种结果", expanded=True):
                        st.dataframe(df_tier2[['表现型_Full', '概率', '链接', '_gene_count']].rename(columns={'表现型_Full': '表现型'}),
                                     column_config=common_config, use_container_width=True, hide_index=True)
                        
                # 渲染 Tier 3 (默认折叠)
                if not df_tier3.empty:
                    with st.expander(f"📂 其他副产物 (Others) - {len(df_tier3)} 种结果", expanded=False):
                        st.dataframe(df_tier3[['表现型_Full', '概率', '链接', '_gene_count']].rename(columns={'表现型_Full': '表现型'}),
                                     column_config=common_config, use_container_width=True, hide_index=True)

# --- 3. F2 选育推演 ---
st.divider()
st.markdown("#### 3. F2 选育推演 (回交/近亲)")

if not any(df is not None and not df.empty for df in f1_dfs.values()):
    st.info("F1 无数据，无法进行推演。")
else:
    c1, c2, c3 = st.columns([1, 1, 1.5])

    # 1. 选留种
    with c1:
        st.markdown("**:one: 留哪条 F1?**")
        source_clutch = st.selectbox("来源:", ["母蛇 A 的后代", "母蛇 B 的后代", "母蛇 C 的后代"])
        clutch_key_map = {"母蛇 A 的后代": "A", "母蛇 B 的后代": "B", "母蛇 C 的后代": "C"}
        clutch_key = clutch_key_map[source_clutch]
        
        current_df = f1_dfs.get(clutch_key)
        if current_df is not None and not current_df.empty:
            options = []
            for idx, row in current_df.iterrows():
                clean_label = row['表现型_Full'].replace("\n", " ").replace("**", "").split(">>>")[-1].strip()
                options.append(f"{clean_label} ({row['概率']:.1f}%)")
                
            sel_idx = st.selectbox("个体:", range(len(current_df)), format_func=lambda x: options[x])
            holdback_geno_dict = dict(current_df.iloc[sel_idx]['_geno_dict'])
            holdback_geno = {gid: holdback_geno_dict.get(gid, 0) for gid in selected_gene_ids}
        else:
            st.warning("该来源无数据")
            st.stop()

    # 2. 选配偶
    with c2:
        st.markdown("**:two: 配给谁?**")
        partner_map = {
            "回交 - 公蛇 (父亲)": male_geno,
            "回交 - 母蛇 A (亲妈/姨妈)": females_geno["A"],
            "回交 - 母蛇 B (姨妈)": females_geno["B"],
            "回交 - 母蛇 C (姨妈)": females_geno["C"],
            "同窝互配 (Sibling/近亲)": holdback_geno 
        }
        partner_choice = st.radio("配偶选择:", list(partner_map.keys()))
        partner_geno = partner_map[partner_choice]

    # 3. 结果 & 风控
    with c3:
        st.markdown("**:three: F2 结果**")
        df_f2 = calculate_offspring(holdback_geno, partner_geno)
        
        f2_risks = check_genetic_risks(df_f2, selected_gene_ids)
        if f2_risks:
            for r in f2_risks: st.markdown(f"<div class='risk-alert'>{r}</div>", unsafe_allow_html=True)
            
        df_f2['表现型'] = df_f2.apply(lambda row: format_label_with_combo(row, selected_gene_ids, simplified=False), axis=1)
        df_f2['链接'] = df_f2.apply(lambda row: generate_mm_link(dict(row['_geno_dict'])), axis=1)
        
        st.dataframe(
            df_f2[['表现型', '概率', '链接']], 
            column_config={
                "概率": st.column_config.NumberColumn(format="%.1f%%", width="small"),
                "链接": st.column_config.LinkColumn("图鉴", display_text="MorphMarket", width="small")
            },
            use_container_width=True,
            hide_index=True,
            height=300
        )
