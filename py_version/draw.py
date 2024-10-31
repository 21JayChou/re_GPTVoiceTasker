# from pyecharts import options as opts
# from pyecharts.charts import Graph
#
# # 定义节点和边
# # nodes = [
# #     {"name": "结点1", "symbol_size": 40, "symbol": "image://C://Users//25061//Desktop//re_GPTVoiceTasker//py_version//data//com.tencent.mm//screenshots//screen_2024-10-31_133305.png"},
# #     {"name": "结点2", "symbol_size": 20, "symbol": "image://C:\\Users\\25061\Desktop\\re_GPTVoiceTasker\\py_version\\data\\com.tencent.mm\\screenshots\\screen_2024-10-31_133318.png"},
# #     # ... 其他节点
# # ]
# nodes = [
#     {"name": "结点1", "symbol_size": 1000, "symbol": "rectangle"},
#     {"name": "结点2", "symbol_size": 1000, "symbol": "rectangle"},
#     # ... 其他节点
# ]
#
# links = [
#     {"source": "结点1", "target": "结点2"},
#     # ... 其他边
# ]
#
# # 创建Graph对象并添加数据
# g = (
#     Graph()
#     .add(
#         "",  # 系列名称
#         nodes,
#         links,
#         repulsion=8000
#     )
#     .set_global_opts(title_opts=opts.TitleOpts(title="Graph-基本示例"))
#     .render("graph.html")
# )

from pyecharts import options as opts
from pyecharts.charts import Graph

nodes = [
    {"name": "结点1", "symbolSize": 10, "symbol": "image://data/com.tencent.mm/screenshots/screen_2024-10-31_133305.png"},
    {"name": "结点2", "symbolSize": 20},
    {"name": "结点3", "symbolSize": 30},
    {"name": "结点4", "symbolSize": 40},
    {"name": "结点5", "symbolSize": 50},
    {"name": "结点6", "symbolSize": 40},
    {"name": "结点7", "symbolSize": 30},
    {"name": "结点8", "symbolSize": 20},
]
links = []
for i in nodes:
    for j in nodes:
        links.append({"source": i.get("name"), "target": j.get("name")})
c = (
    Graph()
    .add("", nodes, links, repulsion=8000)
    .set_global_opts(title_opts=opts.TitleOpts(title="Graph-基本示例"))
    .render("graph.html")
)
