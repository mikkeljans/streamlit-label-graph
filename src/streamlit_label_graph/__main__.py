import sys
import streamlit_label_graph
from streamlit.web import cli as stcli

if __name__ == '__main__':
    sys.argv = ["streamlit", "run", streamlit_label_graph.__file__]
    sys.exit(stcli.main())