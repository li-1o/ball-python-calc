import streamlit as st
import pandas as pd
import itertools
from collections import defaultdict
from datetime import timedelta, date

# ================= 0. 基础配置 =================
st.set_page_config(page_title="球蟒繁育系统 Ultimate", layout="wide")

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .stDataFrame { font-size: 13px; }
    a { text-decoration: none; font-weight: bold; color: #0068c9; }
    /* 风险提示样式 */
    .risk-alert { 
        padding: 8px; 
        background-color: #fee2e2; 
        color: #b91c1c; 
        border-radius: 4px; 
        border-left: 4px solid #ef4444;
        margin-bottom: 8px;
        font-size: 13px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ================= 1. 数据库 (基因 + 风险) =================
GENE_DB = {
    # BEL组
    "Mojave": {"cn": "莫哈维", "type": "显性", "group": "BEL"},
    "Lesser": {"cn": "白金", "type": "显性", "group": "BEL"},
    "Butter": {"cn": "黄油", "type": "显性", "group": "BEL"},
    "Bamboo": {"cn": "竹子", "type": "显性", "group": "BEL"},
    "Russo": {"cn": "卢瑟", "type": "显性", "group": "BEL"},
    # 常用显性
    "Banana": {"cn": "香蕉 (性连锁)", "type": "显性"},
    "Pastel": {"cn": "蜡笔", "type": "显性"},
    "Black Pastel": {"cn": "黑蜡笔", "type": "显性"},
    "Enchi": {"cn": "安奇", "type": "显性"},
    "Yellow Belly": {"cn": "黄腹", "type": "显性"},
    "Fire": {"cn": "火", "type": "显性"},
    "Spotnose": {"cn": "斑鼻", "type": "显性"},
    "OD": {"cn": "橙梦", "type": "显性"},
    "Cypress": {"cn": "柏树", "type": "显性"},
    "Champagne": {"cn": "香槟", "type": "显性"},
    "Spider": {"cn": "蜘蛛", "type": "显性"},
    "Red Stripe": {"cn": "红条", "type": "显性"},
    "Mahogany": {"cn": "红木", "type": "显性"},
    "GHI": {"cn": "GHI", "type": "显性"},
    # 隐性
    "Clown": {"cn": "小丑", "type": "隐性"},
    "Pied": {"cn": "派", "type": "隐性"},
    "DG": {"cn": "沙幽 (DG)", "type": "隐性"},
    "Monsoon": {"cn": "季风", "type": "隐性"},
    "Ghost": {"cn": "幽灵", "type": "隐性"},
    "Albino": {"cn": "白化", "type": "隐性"},
    "Lavender": {"cn": "薰衣草", "type": "隐性"},
    "Axanthic": {"cn": "缺黄", "type": "隐性"},
    "Ultramel": {"cn": "超焦", "type": "隐性"},
    "Puzzle": {"cn": "拼图", "type": "隐性"},
    "Sunset": {"cn": "日落", "type": "隐性"},
    "Tri-Stripe": {"cn": "三条纹", "type": "隐性"},
}

# 风险库
RISK_DB = {
    "Black Pastel": {2: "⚠️ 严重风险: Super Black Pastel 极易出现脊柱弯曲 (Kinking) 和鸭嘴畸形。"},
    "Spider": {1: "⚠️ 注意: 蜘蛛基因携带神经系统问题 (Wobble)。", 2: "💀 致死风险: Super Spider 为致死基因。"},
    "Champagne": {2: "💀 致死风险: Super Champagne 为致死基因。"},
    "Spotnose": {2: "⚠️ 风险: Super Spotnose 可能伴随神经问题。"},
    "GHI": {2: "⚠️ 风险: Super GHI 生长缓慢且可能存在致死风险。"},
}

OPT_WILD = "无"
OPT_HET = "单显/杂合 (Het)"
OPT_SUPER = "超级/纯合 (Super/Visual)"
STATUS_MAP = {OPT_WILD: 0, OPT_HET: 1, OPT_SUPER: 2}

# ================= 2. 核心算法 =================

def check_genetic_risks(df, active_gene_ids):
    """检查结果中的风险"""
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
    """BEL 命名逻辑"""
    bel_count = 0
    for gid, score in active_genes_dict.items():
        if score > 0 and GENE_DB.get(gid, {}).get("group") == "BEL":
            bel_count += score
    if bel_count >= 2: return "**BEL (蓝眼白路)**"
    return None

def generate_mm_link(active_genes_dict):
    """MorphMarket 链接"""
    search_terms = [gid for gid, score in active_genes_dict.items() if score > 0]
    if not search_terms: return "https://www.morphmarket.com/us/c/reptiles/pythons/ball-pythons?trait_form=Normal"
    query = "&genes=" + "+".join(search_terms)
    return f"https://www.morphmarket.com/us/c/reptiles/pythons/ball-pythons?{query}"

def get_gene_prob_matrix(male, female, gene_ids):
    matrix_data = []
    for gid in gene_ids:
        m_score = male.get(gid, 0)
        f_score = female.get(gid, 0)
        
        def get_gamete_probs(score):
            if score == 2: return {1: 1.0} 
            if score == 1: return {0: 0.5, 1: 0.5} 
            return {0: 1.0} 
            
        m_probs = get_gamete_probs(m_score)
        f_probs = get_gamete_probs(f_score)
        
        offspring_probs = defaultdict(float)
        for m_val, m_p in m_probs.items():
            for f_val, f_p in f_probs.items():
                offspring_probs[m_val + f_val] += (m_p * f_p)
                
        row = {"基因": gid, "原色": offspring_probs.get(0, 0.0), "Het": offspring_probs.get(1, 0.0), "Super": offspring_probs.get(2, 0.0)}
        matrix_data.append(row)
    return pd.DataFrame(matrix_data).set_index("基因")

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
        results.append(row)
    return pd.DataFrame(results).sort_values('概率', ascending=False).reset_index(drop=True)

def format_label_with_combo(row, active_gene_ids):
    geno_dict = dict(row['_geno_dict'])
    combo_name = apply_combo_rules(geno_dict)
    labels = []
    for gene_id in active_gene_ids:
        val = geno_dict.get(gene_id, 0)
        if val == 0: continue
        gene_info = GENE_DB.get(gene_id, {"type": "隐性"})
        if "隐性" in gene_info["type"]: suffix = "**(Visual)**" if val == 2 else "(Het)"
        else: suffix = "**(Super)**" if val == 2 else "" 
        labels.append(f"{gene_id} {suffix}")
    base_label = ", ".join(labels) if labels else "Wild Type"
    if combo_name: return f"{combo_name}\n({base_label})"
    return base_label

# ================= 3. 界面布局 =================

st.title("球蟒繁育系统 Ultimate")

# --- 侧边栏：繁育日历 ---
with st.sidebar:
    st.header("📅 生产排期计算")
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
    st.success(f"💰 **上市**: {d_sale.strftime('%Y-%m-%d')}")
    st.caption("*仅供参考，受温度/个体影响较大")

# --- 1. 繁殖组设定 ---
st.markdown("#### 1. 繁殖组设定")
default_genes = []
for g in ["Black Pastel", "Clown"]: 
    target = f"{g} ({GENE_DB[g]['cn']})"
    if target in [f"{k} ({v['cn']})" for k, v in GENE_DB.items()]: default_genes.append(target)

selected_display_names = st.multiselect("添加基因池:", [f"{k} ({v['cn']})" for k, v in GENE_DB.items()], default=default_genes, label_visibility="collapsed")
if not selected_display_names: st.stop()

selected_gene_ids = [name.split(" (")[0] for name in selected_display_names]

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

st.markdown("#### 2. 全景分析 (含风控预警)")

col_a, col_b, col_c = st.columns(3, gap="medium")
f1_dfs = {}

def render_clutch_column(col, name, title_color):
    with col:
        st.markdown(f":{title_color}[**母蛇 {name} 的后代**]")
        
        # 1. 计算
        df = calculate_offspring(male_geno, females_geno[name])
        prob_matrix = get_gene_prob_matrix(male_geno, females_geno[name], selected_gene_ids)
        
        # 2. 风控
        risks = check_genetic_risks(df, selected_gene_ids)
        if risks:
            for r in risks: st.markdown(f"<div class='risk-alert'>{r}</div>", unsafe_allow_html=True)
        
        # 3. 矩阵
        st.dataframe(prob_matrix.style.format("{:.0%}").background_gradient(cmap="Greens", axis=None), use_container_width=True)
        
        # 4. 列表
        if not df.empty:
            df['表现型'] = df.apply(lambda row: format_label_with_combo(row, selected_gene_ids), axis=1)
            df['链接'] = df.apply(lambda row: generate_mm_link(dict(row['_geno_dict'])), axis=1)

            def highlight(row):
                d = dict(row['_geno_dict'])
                is_hit = any(d.get(gid) == 2 for gid in selected_gene_ids)
                is_bel = apply_combo_rules(d) is not None
                if is_bel: return ['background-color: #dbeafe' for _ in row] 
                if is_hit: return ['background-color: #fcf6bd' for _ in row] 
                return ['' for _ in row]

            st.dataframe(
                df[['表现型', '概率', '链接']],
                column_config={
                    "概率": st.column_config.NumberColumn(format="%.1f%%", width="small"),
                    "表现型": st.column_config.Column(width="medium"),
                    "链接": st.column_config.LinkColumn("图鉴", display_text="🔍", width="small")
                },
                use_container_width=True,
                hide_index=True,
                height=350
            )
            return df
    return None

f1_dfs["A"] = render_clutch_column(col_a, "A", "blue")
f1_dfs["B"] = render_clutch_column(col_b, "B", "orange")
f1_dfs["C"] = render_clutch_column(col_c, "C", "red")


# --- 3. F2 选育推演 (功能回归版) ---
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
        clutch_key = source_clutch.split(" ")[1]
        
        current_df = f1_dfs.get(clutch_key)
        if current_df is not None and not current_df.empty:
            options = []
            for idx, row in current_df.iterrows():
                clean_label = row['表现型'].replace("\n", " ").replace("**", "")
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
            "同窝互配 (Sibling/近亲)": holdback_geno # 简化为配同样基因型
        }
        partner_choice = st.radio("配偶选择:", list(partner_map.keys()))
        partner_geno = partner_map[partner_choice]

    # 3. 结果 & 风控
    with c3:
        st.markdown("**:three: F2 结果**")
        df_f2 = calculate_offspring(holdback_geno, partner_geno)
        
        # F2 也要查风控！(例如互配黑蜡笔)
        f2_risks = check_genetic_risks(df_f2, selected_gene_ids)
        if f2_risks:
            for r in f2_risks: st.markdown(f"<div class='risk-alert'>{r}</div>", unsafe_allow_html=True)
            
        df_f2['表现型'] = df_f2.apply(lambda row: format_label_with_combo(row, selected_gene_ids), axis=1)
        df_f2['链接'] = df_f2.apply(lambda row: generate_mm_link(dict(row['_geno_dict'])), axis=1)
        
        st.dataframe(
            df_f2[['表现型', '概率', '链接']],
            column_config={
                "概率": st.column_config.NumberColumn(format="%.1f%%", width="small"),
                "链接": st.column_config.LinkColumn("图鉴", display_text="🔍", width="small")
            },
            use_container_width=True,
            hide_index=True,
            height=250
        )