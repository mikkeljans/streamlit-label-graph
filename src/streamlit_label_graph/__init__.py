from dataclasses import asdict, dataclass
from datetime import date, datetime
import json
from pathlib import Path
import pprint
from typing import Any, List, Optional, TypedDict, Union

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
    left: Union[float, datetime]
    right: Union[float, datetime]

class LabelResult(TypedDict):
    series: Optional[pd.Series]
    labels: List[Label]
    selection: List[str]
    deleted: List[str]

def datetime_serial (obj):
    """ serialize datetime as milliseconds """

    if isinstance(obj, datetime):
        return obj.timestamp() * 1000
    raise TypeError ("Type %s not serializable" % type(obj))

_default_config: LabelConfig = {'categories': []}
_default_result: LabelResult = {'labels': [], 'selection': [], 'series': None, 'deleted': []}
def label_graph(
    figure_or_data, config: LabelConfig=_default_config,
    labels: Optional[List[Label]] = None, key = None
) -> LabelResult:
    kwargs = {}
    plotly_config = {} 
    plotly_config.setdefault("showLink", kwargs.get("show_link", False))
    plotly_config.setdefault("linkText", kwargs.get("link_text", False))
    
    figure = plotly.tools.return_figure_from_figure_or_data(
        figure_or_data, validate_figure=True
    )
    
    # TODO: this assumes there's always one xaxis, with one datapoint
    xaxis = [x[x['xaxis']] for x in figure['data']][0]
    value = None if not len(xaxis) else xaxis[0]

    # TODO: support "date" ?
    is_datetime = isinstance(value, datetime)
    is_series = isinstance(xaxis, (pd.Series, np.ndarray,))

    plotly_spec = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
    plotly_config = json.dumps(plotly_spec)
    
    component_value: LabelResult = _component_func(
        key=key,
        plotly_spec=plotly_spec, plotly_config=plotly_config, 
        config=json.dumps(config), labels=json.dumps(labels, default=datetime_serial)
    )
    if component_value is None:
        component_value = _default_result.copy()
        component_value['labels'] = labels or []
    
    if is_datetime:
        for label in component_value['labels']:
            if isinstance(label['left'], (float, int)):
                label['left'] = datetime.fromtimestamp(label['left'] / 1000)
            if isinstance(label['right'], (float, int)):
                label['right'] = datetime.fromtimestamp(label['right'] / 1000)

    if is_series:
        result_labels = component_value['labels']
        df = pd.DataFrame({'input': xaxis.copy(), 'output': pd.Series([None] * len(xaxis))})
        for label in result_labels:
            c = df['input']
            df.loc[
                (c >= label['left']) & (c <= label['right']), 'output'
            ] = label['category']
        component_value['series'] = df['output']
    else:
        component_value['series'] = None # TODO: support non-dataframe input ?

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
def _test_data_numpy ():
    x = np.linspace(0, 365)
    y = np.sin(2 * np.pi * x / 365) + np.random.normal(0, 0.1, size=len(x))
    return pd.DataFrame({'date': x, 'temperature': y})

if not 'DB' in st.session_state:
    st.session_state['DB'] = [
        {
            "key": "test-01", "category": "HOT", 
            "group": "test0",
            "left": datetime(2022,2,1), 
            "right": datetime(2022,6,1)
        },
        {
            "key": "test-02", "category": "COLD",
            "group": "test1", 
            "left": datetime(2022,9,1), 
            "right": datetime(2022,12,1)
        }
    ]

def _get_db ():
    return st.session_state['DB']

def _get_labels (group):
    return [x for x in _get_db() if x['group'] == group]

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
    """
    * Use Ctrl + Mouse-drag to create a new label
    * Right click on a label to set the category
    """
    df = _test_data_timedate()
    group = st.radio('select labels', ['test0', 'test1'])
    initial_labels = _get_labels(group)

    labels = label_graph(
        px.line(df, x=df['date'], y=df['temperature']), config, labels=initial_labels, key=group
    )
    df['label'] = labels['series']

    
    db = _get_db()
    db_labels = {l['key']: l for l in db}
    for l in labels['labels']:
        label: Any = l.copy()
        label.setdefault('group', group)
        if label['group'] == group:
            db_labels[label['key']] = label
    
    for removed_label in labels['deleted']:
        if removed_label in db_labels:
            del db_labels[removed_label]

    st.session_state['DB'] = list(db_labels.values())
    st.write(st.session_state['DB'])
    

    st.write('### Output:')
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Line(x=df['date'], y=df['temperature'], name='temperature'), secondary_y=False)
    fig.add_trace(go.Line(x=df['date'], y=df['label'], name='label'), secondary_y=True)
    st.write(fig)    
    st.write(labels)
    st.write(df)


if __name__ == "__main__":
    main()
