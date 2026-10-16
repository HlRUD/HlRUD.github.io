function _defineProperty(obj, key, value) {if (key in obj) {Object.defineProperty(obj, key, { value: value, enumerable: true, configurable: true, writable: true });} else {obj[key] = value;}return obj;}class Counter extends React.Component {constructor(...args) {super(...args);_defineProperty(this, "state",
    { count: 0 });_defineProperty(this, "increment",
    () => this.setState({ count: this.state.count + 1 }));_defineProperty(this, "decrement",
    () => this.state.count > 0 && this.setState({ count: this.state.count - 1 }));_defineProperty(this, "reset",
    () => this.state.count !== 0 && this.setState({ count: 0 }));}
  render() {
    return (
      React.createElement("div", null,
      React.createElement("h1", null, "کلیک کنید !"),
      React.createElement("p", null, this.state.count),
      React.createElement("div", null,
      React.createElement("button", { onClick: this.increment }, "+"),
      React.createElement("button", { onClick: this.decrement }, "-"),
      React.createElement("button", { onClick: this.reset }, "ریست")),
      React.createElement("small", null, "")));
  }}
;
ReactDOM.render(React.createElement(Counter, null), document.getElementById('app'));