from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, List, Optional, TypedDict

import streamlit as st
import streamlit.components.v1 as components

frontend_dir = (Path(__file__).parent / "frontend").absolute()
_component_func = components.declare_component(
	"label_graph", path=str(frontend_dir)
)


import plotly.tools
import plotly.utils
import pandas as pd
import numpy as np
import plotly.express as px


class Category(TypedDict):
    key: str
    color: str

class LabelConfig(TypedDict):
    categories: List[Category]

class Label(TypedDict):
    key: str
    category: str
    left: float
    right: float

class LabelResult(TypedDict):
    labels: List[Label]


_default_config: LabelConfig = {'categories': []}
_default_result: LabelResult = {'labels': []}
def label_graph(
    figure_or_data, config: LabelConfig=_default_config, key: Optional[str] = None
) -> LabelResult:
    kwargs = {}
    plotly_config = {} 
    plotly_config.setdefault("showLink", kwargs.get("show_link", False))
    plotly_config.setdefault("linkText", kwargs.get("link_text", False))
    
    figure = plotly.tools.return_figure_from_figure_or_data(
        figure_or_data, validate_figure=True
    )
    plotly_spec = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
    plotly_config = json.dumps(plotly_config)
    
    component_value = _component_func(
        key=key, plotly_spec=plotly_spec, plotly_config=plotly_config, 
        config=json.dumps(config)
    )
    if component_value is None:
        return _default_result
    
    return component_value


def label_dataframes (df, labels):
    result = []
    for label in labels['labels']:
        label_df = df[(df['x'] >= label['left']) & (df['x'] <= label['right'])]
        result.append(label_df)
    return result

@st.cache_data
def _test_data_timedate ():
    x = pd.date_range(start='2022-01-01', end='2022-12-31', freq='D')
    y = np.sin(2 * np.pi * x.dayofyear / 365) + np.random.normal(0, 0.1, size=len(x))
    return pd.DataFrame({'date': x, 'temperature': y})

@st.cache_data
def _test_data ():
    x = np.linspace(0, 365)
    y = np.sin(2 * np.pi * x / 365) + np.random.normal(0, 0.1, size=len(x))
    return pd.DataFrame({'date': x, 'temperature': y})
    
def apply_label_column (df: pd.DataFrame, labels: LabelResult, x: str, name: str='label'):
    df[name] = pd.Series(dtype='string')
    
    for label in labels['labels']:
        c = df[x]
        if df[x].dtype == 'datetime64[ns]':
            c = df[x].astype('int64') / 10**6
        df.loc[
            (c >= label['left']) & (c <= label['right']), name
        ] = label['category']
    return df

def main():
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    st.write("## Label Graph")
    config: LabelConfig = {
        'categories': [
            {'key': 'HOT', 'color': 'rgba(255 110 110,0.1)'},
            {'key': 'COLD', 'color': 'rgba(110,110,255,0.1)'}
        ]
    }
    st.code("""
import plotly.express as px
import pandas as pd
from streamlit_label_graph import label_graph, LabelConfig

config: LabelConfig = {
    'categories': [
        {'key': "HOT", 'color': 'rgba(255 110 110,0.1)'},
        {'key': 'COLD', 'color': "rgba(110,110,255,0.1)"}
    ]
}
df = pd.DataFrame({'date': .., 'temperature': ..})
figure = px.line(df, x=df['date'], y=df['temperature'])
labels = label_graph(figure, config)
# -> [{"key": "..", "category": "HOT", "left": .., "right": ..}, {...}]
    """, language='python')
    """
    * Use Ctrl + Mouse-drag to create a new label
    * Right click on a label to set the category
    """
    df = _test_data_timedate()
    labels = label_graph(
        px.line(df, x=df['date'], y=df['temperature']), config
    )

    st.write('### Apply label category to dataframe')
    df = apply_label_column(df, labels, 'date')
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Line(x=df['date'], y=df['temperature'], name='temperature'), secondary_y=False)
    fig.add_trace(go.Line(x=df['date'], y=df['label'], name='label'), secondary_y=True)
    st.write(fig)

    st.write('### Output:')
    st.write(labels)
    st.write(df)
    

if __name__ == "__main__":
    main()
