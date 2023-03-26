# streamlit-label-graph

Plotly graph for labelling timeserie data

```sh
pip install streamlit-label-graph
```

```python
import streamlit as st

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from streamlit_label_graph import label_graph, LabelConfig


@st.cache_data
def weather_data ():
    x = pd.date_range(start='2022-01-01', end='2022-12-31', freq='D')
    y = np.sin(2 * np.pi * x.dayofyear / 365) + np.random.normal(0, 0.1, size=len(x))
    return pd.DataFrame({'date': x, 'temperature': y})

config: LabelConfig = {
    'categories': [
        {'key': 'HOT', 'color': 'rgba(255 110 110,0.1)'},
        {'key': 'COLD', 'color': 'rgba(110,110,255,0.1)'}
    ]
}
df = weather_data()

figure = px.line(df, x=df['date'], y=df['temperature'])
labels = label_graph(figure, config)
df['label'] = labels['series']

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Line(x=df['date'], y=df['temperature'], name='temperature'), secondary_y=False)
fig.add_trace(go.Line(x=df['date'], y=df['label'], name='label'), secondary_y=True)
st.write(fig)
st.write(labels)

```

* Use Ctrl + Mouse-drag to create a new label
* Right click on a label to set the category

![Demo](demo_image.png)


## Run demo

```sh
python -m streamlit_label_graph
```