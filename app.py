import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, callback
import dash
from factoranalysis import pfa

C = dict(
    bg        = "#060B11",
    surface   = "#0D1117",
    surface2  = "#141B24",
    border    = "#1E2D3D",
    border2   = "#243447",
    accent    = "#00C2FF",
    accent2   = "#00FFB3",
    warn      = "#FF9500",
    danger    = "#FF3B30",
    muted     = "#4A5E72",
    text      = "#B8C9D9",
    text_hi   = "#E8F0F7",
    text_lo   = "#3D5166",
)

PALETTE = [
    "#00C2FF", "#00FFB3", "#FF9500", "#FF3B30",
    "#BF5AF2", "#30D158", "#FFD60A", "#5E9CF5",
    "#FF6B6B", "#4ECDC4",
]

FONT    = "'IBM Plex Mono', 'Courier New', monospace"
FONT_UI = "'IBM Plex Sans', 'Helvetica Neue', sans-serif"

PLOT_BASE = dict(
    paper_bgcolor = C["surface"],
    plot_bgcolor  = C["surface"],
    font          = dict(family=FONT, size=11, color=C["text"]),
    hovermode     = "x unified",
    hoverlabel    = dict(bgcolor="#0D1117", font_color=C["accent"],
                         font_family=FONT, bordercolor=C["border2"]),
    margin        = dict(l=60, r=50, t=45, b=50),
    legend        = dict(orientation="h", x=0.5, y=1.04,
                         xanchor="center", yanchor="bottom",
                         bgcolor="rgba(0,0,0,0)",
                         font=dict(size=10)),
    xaxis         = dict(showgrid=True,  gridcolor=C["border"],  gridwidth=1,
                         linecolor=C["border2"], showline=True,
                         tickfont=dict(size=10), zeroline=False),
    yaxis         = dict(showgrid=True,  gridcolor=C["border"],  gridwidth=1,
                         linecolor=C["border2"], showline=True,
                         tickfont=dict(size=10),
                         zeroline=True, zerolinecolor=C["border2"], zerolinewidth=1),
    title         = dict(font=dict(family=FONT_UI, size=14, color=C["text_hi"]),
                         x=0, xanchor="left", pad=dict(l=4)),
)


def _axis_style():
    return dict(showgrid=True, gridcolor=C["border"], gridwidth=1,
                linecolor=C["border2"], showline=True,
                tickfont=dict(size=10, family=FONT),
                zeroline=True, zerolinecolor=C["border2"], zerolinewidth=1)


def build_decomposition(stocks_sel=None):
    data = pfa.decomposition()
    expvar, comps = data["expvar"], data["comps"]
    if stocks_sel:
        comps = comps.loc[comps.index.isin(stocks_sel)]

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["COMPONENT LOADINGS  ·  TOP 3 PCs",
                        "CUMULATIVE EXPLAINED VARIANCE"],
        vertical_spacing=0.18,
        row_heights=[0.58, 0.42],
    )
    for i, pc in enumerate(comps.columns[:3]):
        fig.add_trace(go.Scatter(
            x=comps.index, y=comps[pc], name=pc, mode="lines+markers",
            line=dict(color=PALETTE[i], width=2),
            marker=dict(size=6, symbol="circle",
                        line=dict(width=1.5, color=C["surface"])),
            hovertemplate="<b>%{y:.4f}</b><extra>%{fullData.name}</extra>",
        ), row=1, col=1)

    bar_colors = [f"rgba({int(c[1:3],16)},{int(c[3:5],16)},{int(c[5:7],16)},0.85)"
                  for c in [PALETTE[0]] * len(expvar)]
    fig.add_trace(go.Bar(
        x=expvar.index, y=expvar, showlegend=False,
        marker=dict(color=expvar, colorscale=[[0, C["border2"]], [1, C["accent"]]],
                    line=dict(width=0)),
        hovertemplate="<b>%{y:.4f}</b><extra></extra>",
    ), row=2, col=1)

    ax = _axis_style()
    fig.update_xaxes(**ax, title=dict(text="PORTFOLIO COMPONENTS", font_size=10,
                                      font_family=FONT_UI), row=1, col=1)
    fig.update_xaxes(**ax, title=dict(text="PRINCIPAL COMPONENTS",  font_size=10,
                                      font_family=FONT_UI), row=2, col=1)
    fig.update_yaxes(**ax, title=dict(text="LOADING", font_size=10,
                                      font_family=FONT_UI), row=1, col=1)
    fig.update_yaxes(**ax, title=dict(text="EXP. VARIANCE", font_size=10,
                                      font_family=FONT_UI), row=2, col=1)

    fig.update_layout(**PLOT_BASE, height=680)
    
    for ann in fig.layout.annotations:
        ann.update(font=dict(family=FONT_UI, size=11, color=C["muted"]),
                   x=0, xanchor="left")
    return fig


def build_betas(stocks_sel=None, date_range=None):
    betas = pfa.get_betas()
    if date_range:
        betas = betas.loc[date_range[0]:date_range[1]]
    cols = [c for c in betas.columns if c in stocks_sel] if stocks_sel else betas.columns

    fig = go.Figure()
    for i, stock in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=betas.index, y=betas[stock], name=stock, opacity=0.65,
            line=dict(width=1.3, color=PALETTE[i % len(PALETTE)]),
            hovertemplate="<b>%{y:.4f}</b><extra>%{fullData.name}</extra>",
        ))
    fig.add_trace(go.Scatter(
        x=betas.index, y=betas[cols].mean(axis=1),
        name="MEAN β",
        line=dict(color=C["warn"], width=2.2, shape="spline"),
        hovertemplate="<b>%{y:.4f}</b><extra>MEAN β</extra>",
    ))
    fig.add_hline(y=1, line=dict(width=1.2, dash="dash", color=C["muted"]),
                  annotation=dict(text="β = 1.0", font=dict(size=10,
                  color=C["muted"], family=FONT),
                  x=1.01, xanchor="left"))

    fig.update_layout(**PLOT_BASE, height=420,
                      xaxis_title="DATE", yaxis_title="BETA  (β)")
    return fig


def build_zscores(stocks_sel=None, date_range=None):
    zs = pfa.get_zscores()
    if date_range:
        zs = zs.loc[date_range[0]:date_range[1]]
    cols = [c for c in zs.columns if c in stocks_sel] if stocks_sel else zs.columns

    fig = go.Figure()

    for sigma, alpha, col in [(2, 0.06, C["danger"]), (1, 0.09, C["warn"])]:
        fig.add_hrect(y0=-sigma, y1=sigma,
                      fillcolor=col, opacity=alpha, line_width=0, layer="below")
        for sign in [1, -1]:
            fig.add_hline(y=sign * sigma,
                          line=dict(width=0.8, dash="dot", color=col),
                          annotation=dict(
                              text=f"{sign*sigma:+d}σ",
                              font=dict(size=9, color=col, family=FONT),
                              x=1.01, xanchor="left"))

    for i, stock in enumerate(cols):
        fig.add_trace(go.Scatter(
            x=zs.index, y=zs[stock], name=stock, opacity=0.65,
            line=dict(width=1.3, color=PALETTE[i % len(PALETTE)]),
            hovertemplate="<b>%{y:.4f}σ</b><extra>%{fullData.name}</extra>",
        ))
    fig.add_trace(go.Scatter(
        x=zs.index, y=zs[cols].mean(axis=1),
        name="MEAN Z",
        line=dict(color=C["accent2"], width=2.2, shape="spline"),
        hovertemplate="<b>%{y:.4f}σ</b><extra>MEAN Z</extra>",
    ))

    fig.update_layout(**PLOT_BASE, height=420,
                      xaxis_title="DATE", yaxis_title="Z-SCORE  (σ)")
    return fig


def _label(text, small=False):
    return html.Span(text, style={
        "fontFamily": FONT_UI, "fontSize": "10px" if small else "11px",
        "fontWeight": "600", "letterSpacing": "0.12em",
        "color": C["muted"], "textTransform": "uppercase",
    })


def _divider():
    return html.Hr(style={"borderColor": C["border"], "margin": "12px 0"})


def _stat_card(label, value, color=None):
    return html.Div([
        html.Div(label, style={"fontFamily": FONT_UI, "fontSize": "9px",
                               "letterSpacing": "0.1em", "color": C["muted"],
                               "textTransform": "uppercase", "marginBottom": "2px"}),
        html.Div(value, style={"fontFamily": FONT, "fontSize": "15px",
                               "fontWeight": "600",
                               "color": color or C["accent"]}),
    ], style={"padding": "10px 14px", "background": C["surface2"],
              "border": f"1px solid {C['border']}", "borderRadius": "4px",
              "minWidth": "90px"})


_betas_full  = pfa.get_betas()
_zs_full     = pfa.get_zscores()
_decomp_full = pfa.decomposition()

ALL_STOCKS   = list(_betas_full.columns)
ALL_DATES    = _betas_full.index
MIN_DATE, MAX_DATE = ALL_DATES.min(), ALL_DATES.max()
DATE_MARKS   = {i: {"label": str(d.date()),
                     "style": {"color": C["muted"], "fontSize": "9px"}}
                for i, d in enumerate(pd.date_range(MIN_DATE, MAX_DATE, periods=5))}


app = Dash(__name__, title="PFA · Portfolio Factor Analysis",
           suppress_callback_exceptions=True)

sidebar = html.Div([

    html.Div([
        html.Div("PFA", style={
            "fontFamily": FONT, "fontSize": "22px", "fontWeight": "700",
            "color": C["accent"], "letterSpacing": "0.15em",
        }),
        html.Div("PORTFOLIO FACTOR ANALYSIS", style={
            "fontFamily": FONT_UI, "fontSize": "8px", "letterSpacing": "0.18em",
            "color": C["muted"], "marginTop": "1px",
        }),
    ], style={"padding": "20px 20px 16px"}),

    _divider(),

    html.Div([
        _label("Navigation"),
        html.Div(id="nav-container", children=[
            html.Button("⬡  DECOMPOSITION",  id="nav-decomp",  n_clicks=0,
                        className="nav-btn nav-active"),
            html.Button("▲  MARKET RISK",    id="nav-betas",   n_clicks=0,
                        className="nav-btn"),
            html.Button("◈  Z-SCORES",       id="nav-zscores", n_clicks=0,
                        className="nav-btn"),
        ], style={"display": "flex", "flexDirection": "column", "gap": "4px",
                  "marginTop": "8px"}),
    ], style={"padding": "0 16px"}),

    _divider(),

    html.Div([
        _label("Stocks"),
        dcc.Dropdown(
            id="stock-select",
            options=[{"label": s, "value": s} for s in ALL_STOCKS],
            value=ALL_STOCKS,
            multi=True,
            placeholder="Select stocks…",
            style={"marginTop": "8px"},
            className="pfa-dropdown",
        ),
        html.Div([
            html.Button("ALL",  id="btn-all",   n_clicks=0, className="mini-btn"),
            html.Button("NONE", id="btn-none",  n_clicks=0, className="mini-btn"),
        ], style={"display": "flex", "gap": "6px", "marginTop": "6px"}),
    ], style={"padding": "0 16px"}),

    _divider(),

    html.Div(id="date-range-section", children=[
        _label("Date Range"),
        dcc.RangeSlider(
            id="date-slider",
            min=0, max=len(ALL_DATES)-1,
            value=[0, len(ALL_DATES)-1],
            marks=DATE_MARKS,
            tooltip={"placement": "bottom",
                     "style": {"color": C["accent"], "fontSize": "10px"}},
            className="pfa-slider",
        ),
    ], style={"padding": "0 16px 8px"}),

    _divider(),

    html.Div(id="stats-panel", style={"padding": "0 16px"}),

], style={
    "width": "240px", "minWidth": "240px",
    "height": "100vh", "overflowY": "auto",
    "background": C["surface"],
    "borderRight": f"1px solid {C['border']}",
    "display": "flex", "flexDirection": "column",
})

main_area = html.Div([


    html.Div([
        html.Div(id="page-title", style={
            "fontFamily": FONT_UI, "fontSize": "13px", "fontWeight": "600",
            "letterSpacing": "0.08em", "color": C["text_hi"],
        }),
        html.Div(id="status-bar", style={
            "fontFamily": FONT, "fontSize": "10px", "color": C["muted"],
        }),
    ], style={
        "display": "flex", "justifyContent": "space-between",
        "alignItems": "center",
        "padding": "10px 24px",
        "borderBottom": f"1px solid {C['border']}",
        "background": C["surface2"],
    }),


    html.Div(id="plot-area", style={"padding": "20px 24px", "flex": "1"}),

], style={"flex": "1", "display": "flex", "flexDirection": "column",
          "overflow": "hidden", "background": C["bg"]})


app.layout = html.Div([
    dcc.Store(id="active-page", data="decomp"),
    sidebar,
    main_area,
], style={
    "display": "flex", "height": "100vh", "overflow": "hidden",
    "background": C["bg"],
})

app.index_string = f"""<!DOCTYPE html>
<html>
<head>
    {{%metas%}}
    <title>{{%title%}}</title>
    {{%favicon%}}
    {{%css%}}
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ background: {C["bg"]}; color: {C["text"]}; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-track {{ background: {C["surface"]}; }}
        ::-webkit-scrollbar-thumb {{ background: {C["border2"]}; border-radius: 3px; }}

        .nav-btn {{
            background: transparent;
            border: 1px solid transparent;
            color: {C["muted"]};
            font-family: {FONT};
            font-size: 10px;
            letter-spacing: 0.12em;
            padding: 8px 12px;
            text-align: left;
            cursor: pointer;
            border-radius: 3px;
            transition: all 0.15s;
        }}
        .nav-btn:hover {{
            background: {C["surface2"]};
            border-color: {C["border"]};
            color: {C["text"]};
        }}
        .nav-active {{
            background: {C["surface2"]} !important;
            border-color: {C["accent"]} !important;
            color: {C["accent"]} !important;
        }}

        .mini-btn {{
            background: {C["surface2"]};
            border: 1px solid {C["border"]};
            color: {C["muted"]};
            font-family: {FONT};
            font-size: 9px;
            letter-spacing: 0.1em;
            padding: 4px 10px;
            cursor: pointer;
            border-radius: 3px;
            transition: all 0.15s;
        }}
        .mini-btn:hover {{
            border-color: {C["accent"]};
            color: {C["accent"]};
        }}

        /* Dropdown overrides */
        .pfa-dropdown .Select-control,
        .pfa-dropdown .Select-menu-outer {{
            background-color: {C["surface2"]} !important;
            border-color: {C["border"]} !important;
            color: {C["text"]} !important;
        }}
        .pfa-dropdown .Select-value-label {{
            color: {C["text"]} !important;
            font-family: {FONT} !important;
            font-size: 10px !important;
        }}
        .pfa-dropdown .Select-option {{
            background-color: {C["surface2"]} !important;
            color: {C["text"]} !important;
            font-family: {FONT} !important;
            font-size: 10px !important;
        }}
        .pfa-dropdown .Select-option:hover,
        .pfa-dropdown .Select-option.is-focused {{
            background-color: {C["border"]} !important;
            color: {C["accent"]} !important;
        }}
        .pfa-dropdown .Select-placeholder,
        .pfa-dropdown .Select-input > input {{
            color: {C["muted"]} !important;
            font-family: {FONT} !important;
            font-size: 10px !important;
        }}
        .pfa-dropdown .Select-multi-value-wrapper .Select-value {{
            background: {C["border"]} !important;
            border-color: {C["border2"]} !important;
        }}
        .pfa-dropdown .Select-arrow {{ border-top-color: {C["muted"]} !important; }}

        /* Slider overrides */
        .pfa-slider .rc-slider-rail {{ background: {C["border"]}; }}
        .pfa-slider .rc-slider-track {{ background: {C["accent"]}; }}
        .pfa-slider .rc-slider-handle {{
            border-color: {C["accent"]};
            background: {C["surface"]};
        }}
        .pfa-slider .rc-slider-dot {{ background: {C["border"]}; border-color: {C["border"]}; }}
        .pfa-slider .rc-slider-dot-active {{ border-color: {C["accent"]}; }}
    </style>
</head>
<body>
    {{%app_entry%}}
    <footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body>
</html>"""


@app.callback(
    Output("active-page", "data"),
    Input("nav-decomp",  "n_clicks"),
    Input("nav-betas",   "n_clicks"),
    Input("nav-zscores", "n_clicks"),
    prevent_initial_call=True,
)
def set_active_page(n1, n2, n3):
    triggered = dash.ctx.triggered_id
    return {"nav-decomp": "decomp", "nav-betas": "betas",
            "nav-zscores": "zscores"}.get(triggered, "decomp")


@app.callback(
    Output("nav-decomp",  "className"),
    Output("nav-betas",   "className"),
    Output("nav-zscores", "className"),
    Input("active-page", "data"),
)
def update_nav_classes(page):
    base = "nav-btn"
    active = "nav-btn nav-active"
    return (active if page == "decomp"  else base,
            active if page == "betas"   else base,
            active if page == "zscores" else base)


@app.callback(
    Output("date-range-section", "style"),
    Input("active-page", "data"),
)
def toggle_date_slider(page):
    hidden = {"display": "none"}
    visible = {"padding": "0 16px 8px"}
    return hidden if page == "decomp" else visible


@app.callback(
    Output("stock-select", "value"),
    Input("btn-all",  "n_clicks"),
    Input("btn-none", "n_clicks"),
    prevent_initial_call=True,
)
def quick_select(n_all, n_none):
    return ALL_STOCKS if dash.ctx.triggered_id == "btn-all" else []


@app.callback(
    Output("plot-area",   "children"),
    Output("page-title",  "children"),
    Output("status-bar",  "children"),
    Output("stats-panel", "children"),
    Input("active-page",  "data"),
    Input("stock-select", "value"),
    Input("date-slider",  "value"),
)
def render_page(page, stocks, date_idx):
    sel   = stocks or ALL_STOCKS
    d0    = str(ALL_DATES[date_idx[0]].date())
    d1    = str(ALL_DATES[date_idx[1]].date())
    dr    = (d0, d1)
    n     = len(sel)

    if page == "decomp":
        fig   = build_decomposition(stocks_sel=sel)
        title = "DECOMPOSITION ANALYTICS"
        comps = _decomp_full["comps"]
        expvar= _decomp_full["expvar"]
        top_loading = comps["PC1"].abs().idxmax()
        stats = html.Div([
            _label("Quick Stats"),
            html.Div([
                _stat_card("PC1 VAR", f"{expvar.iloc[0]:.1%}"),
                _stat_card("TOP LOAD", top_loading, C["accent2"]),
            ], style={"display": "flex", "flexWrap": "wrap",
                      "gap": "6px", "marginTop": "8px"}),
        ])
        status = f"STOCKS  {n}  ·  ALL PERIODS"

    elif page == "betas":
        fig   = build_betas(stocks_sel=sel, date_range=dr)
        title = "MARKET RISK ANALYTICS  ·  ROLLING BETA"
        b     = _betas_full.loc[d0:d1, sel] if sel else _betas_full.loc[d0:d1]
        mean  = b.mean().mean()
        above_1 = (b > 1).sum().sum()
        stats = html.Div([
            _label("Quick Stats"),
            html.Div([
                _stat_card("AVG β",    f"{mean:.3f}"),
                _stat_card(">1.0 OBS", str(above_1), C["warn"]),
            ], style={"display": "flex", "flexWrap": "wrap",
                      "gap": "6px", "marginTop": "8px"}),
        ])
        status = f"STOCKS  {n}  ·  {d0}  →  {d1}"

    else: 
        fig   = build_zscores(stocks_sel=sel, date_range=dr)
        title = "STATISTICAL DEVIATION ANALYTICS  ·  Z-SCORES"
        z     = _zs_full.loc[d0:d1, sel] if sel else _zs_full.loc[d0:d1]
        extremes = ((z.abs() > 2).sum().sum())
        mean_z   = z.mean().mean()
        stats = html.Div([
            _label("Quick Stats"),
            html.Div([
                _stat_card("MEAN Z",   f"{mean_z:.3f}"),
                _stat_card("|Z|>2σ",   str(extremes), C["danger"]),
            ], style={"display": "flex", "flexWrap": "wrap",
                      "gap": "6px", "marginTop": "8px"}),
        ])
        status = f"STOCKS  {n}  ·  {d0}  →  {d1}"

    graph = dcc.Graph(
        figure=fig,
        config={"displayModeBar": True, "displaylogo": False,
                "modeBarButtonsToRemove": ["select2d", "lasso2d", "autoScale2d"],
                "toImageButtonOptions": {"filename": f"pfa_{page}",
                                         "format": "png", "scale": 2}},
        style={"height": "100%"},
    )
    return graph, title, status, stats
    
    
if __name__ == "__main__":
    app.run()