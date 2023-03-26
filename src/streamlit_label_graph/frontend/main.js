
function guidGenerator() {
  var S4 = function() {
     return (((1+Math.random())*0x10000)|0).toString(16).substring(1);
  };
  return (S4()+S4()+"-"+S4()+"-"+S4()+"-"+S4()+"-"+S4()+S4()+S4());
}

function _makeMenuItem (label, handler) {
  var node = document.createElement('div')
  node.classList.add('menuItem')
  node.addEventListener('click', handler)
  node.textContent = label
  return node
}

function _blockEvents (e) {
  e.stopPropagation()
  e.stopImmediatePropagation()
  e.preventDefault()
}

const DEFAULT_CATEGORY = {
  key: null, color: 'rgba(0, 0, 0, 0.1)'
}

class GraphController {
  constructor () {
    
  }

  init (labelConfig) {
    this.element = document.getElementById('graph')
    this.menu = document.getElementById('contextMenu');
    this.config = labelConfig
    this.labels = {}
    this.drawRect = {active: false, start: {x: 0, y: 0}, end: {x: 0, y: 0}}
    this.selection = []
    this.deleted = []
    this.initMenu()
    this.initListeners()
  }

  _makeLabel (label) {
    let key = label.key
    let x0 = Math.min(label.left, label.right)
    let x1 = Math.max(label.left, label.right)
    let version = 0
    if (this.labels[key]) version = this.labels[key]._version + 1
    // keep user-input values to make syncing easier
    return {
      ...label, key: key, category: label.category, left: x0, right: x1, top: 0, bottom: 0, _version: version
    }
  }

  initLabels (labels) {
    //console.log('INIT LABELS', labels)
    if (labels == null) return
    let newLabels = {}
    labels.map(label => {
      let version = label._version || 0
      let current = this.labels[label.key]
      if (current && (current._version || 0) > version) {
        newLabels[label.key] = current
      } else if (label.key && label.left != null && label.right != null) {
        newLabels[label.key] = label
      }
    })
    this.labels = newLabels
    this.redraw()
    
  }

  sendValue () {
    let data = {
      labels: this.listLabels(), selection: this.selection.slice(0),
      deleted: this.deleted.slice(0)
    }
    //console.log(' -> ', data)
    Streamlit.setComponentValue(data)
  }

  deleteSelection () {
    this.deleted.push(...this.selection)
    this.redraw()
    this.sendValue()
  }

  listLabels () {
    return Object.values(this.labels).filter(x => !this.deleted.includes(x.key))
  }

  setSelectionCategory (key) {
    let category = this.config.categories.find(x => x.key == key)
    if (!category) throw new Error('no such category: ' + key)
    this.selection = this.selection.filter(x => this.labels[x] != null)
    this.selection.map(x => {
      this.labels[x].category = key
      this.labels[x]._version += 1
    })
    this.redraw()
    this.sendValue()
  }

  makeLabel (left, right) {
    var key = guidGenerator()
    this.labels[key] = this._makeLabel({key: key, category: DEFAULT_CATEGORY.key, left: left, right: right})
    this.sendValue()
    this.redraw()
    return this.labels[key]
  }

  selectLabels (labels) {
    if (!labels) this.selection = []
    else this.selection = labels.map(x => x.key)
    this.redraw()
    this.sendValue()
  }

  labelsAtPoint (coord) {
    let result = this.listLabels().filter(x => {
      return x.left < coord.x && x.right > coord.x
    })
    return result
  }


  initMenu () {
    var content = document.getElementById('menuContent')
    content.addEventListener('click', e => this.showMenu(false, e))
    for (var type of this.config.categories) {
      let node = _makeMenuItem(type.key, this.setSelectionCategory.bind(this, type.key))
      content.appendChild(node)
    }
    let deleteMenuItem = _makeMenuItem('Delete', this.deleteSelection.bind(this))
    deleteMenuItem.classList.add('actionMenuItem')
    content.appendChild(deleteMenuItem)
  }

  showMenu (show, evt) {
    if (show && this.selection.length == 0) return
    var menu = this.menu
    menu.style.left = evt.clientX + 'px';
    menu.style.top = evt.clientY + 'px';
    menu.style.zIndex = 99999
    menu.style.position = 'absolute'
    this.menu.style.display = show ? 'block' : 'none'
  }

  redraw () {
    var shapes = this.listLabels().map(label => {
      let category = this.config.categories.find(x => x.key == label.category) || DEFAULT_CATEGORY
      let shape = {
        type: 'rect', xref: 'x', yref: 'paper',
        x0: label.left, y0: 0, x1: label.right, y1: 1,
        fillcolor: category.color, line: {width: 0}
      }
      if (this.selection.includes(label.key)) {
        shape.line = {
          width: 2, color: 'rgba(100, 100, 100, 0.3)', dash: 'dash'
        }
      }
      return shape
    })
    if (this.drawRect.active) {
      shapes.push({
        type: 'rect', xref: 'x', yref: 'paper',
        x0: this.drawRect.start.x, y0: 0,
        x1: this.drawRect.end.x, y1: 1,
        fillcolor: 'rgba(0, 0, 0, 0.1)',
        line: {
          width: 0,
          color: 'rgba(0, 0, 0, 0.5)'
        }
      })
    }
    Plotly.relayout(this.element, {shapes: shapes});
  }

  getCoords (evt) {
    var elm = this.element
    var layout = elm._fullLayout
    var xaxis = layout.xaxis;
    var yaxis = layout.yaxis;
    var l = layout.margin.l;
    var t = layout.margin.t;
    
    return {x: xaxis.p2c(evt.x - l), y: yaxis.p2c(evt.y - t)}  
  }

  select (evt) {
    this.selectLabels(this.labelsAtPoint(this.getCoords(evt)))
  }

  initListeners () {
    let elm = this.element
    elm.addEventListener('mousedown', evt => {
      this.showMenu(false, evt)
      if (evt.ctrlKey || evt.metaKey) {
        _blockEvents(evt)
        var start = this.getCoords(evt)
        this.drawRect = {...this.drawRect, active: true, start: start, end: {x: 0, y: 0}}
        this.redraw()
      }
    }, {capture: true})

    elm.addEventListener('click', evt => {
      this.select(evt)
    }, {capture: true})

    elm.addEventListener('mouseup', evt => {
      if (this.drawRect.active) {
        this.drawRect.active = false
        var points = [this.drawRect.start.x, this.drawRect.end.x]
        var label = this.makeLabel(Math.min(...points), Math.max(...points))
        setTimeout(() => {
          this.selectLabels([label])
          this.showMenu(true, evt)
        }, 100)
      }
    }, {capture: true})

    elm.addEventListener('mousemove', evt => {
      if (this.drawRect.active) {
        this.drawRect.end = this.getCoords(evt)
        this.redraw()
      }
    });
    elm.addEventListener('contextmenu', evt => {
      _blockEvents(evt)
      this.select(evt)
      this.showMenu(true, evt)
    }, {capture: true});
  }
}

const CTRL = new GraphController()
function onRender(event) {
  
  if (!window.rendered) {
    let pspec = JSON.parse(event.detail.args.plotly_spec)
    let pconfig = JSON.parse(event.detail.args.plotly_config)
    let labelConfig = JSON.parse(event.detail.args.config)
    let labels = JSON.parse(event.detail.args.labels)

    var elm = document.getElementById('graph')
    elm.style.width = '100%'
    pspec.layout.yaxis = {fixedrange: true}
    pspec.layout.scrollZoom = true
    pspec.layout.margin.l = 20
    pspec.layout.margin.r = 20
    
    Plotly.newPlot(elm, pspec, pconfig).then(() => {
      CTRL.init(labelConfig)
      CTRL.initLabels(labels)
      CTRL.sendValue()
    });
    window.rendered = true
  }
}


Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender)
Streamlit.setComponentReady()
Streamlit.setFrameHeight(450)
