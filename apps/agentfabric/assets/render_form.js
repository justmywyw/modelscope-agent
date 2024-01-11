function init__ui_form_generator_renderForm() {
  const setInputValue = (value) => {
    const inputElem = document.getElementById('user_chatbot_input').querySelector('textarea');
    inputElem.value = value;
  }

  // Helper function to create a DOM element with attributes and children
  const createElement = (tag, attributes, ...children) => {
    const element = document.createElement(tag);
    for (const key in attributes) {
      element.setAttribute(key, attributes[key]);
    }
    children.forEach((child) => {
      if (typeof child === 'string') {
        element.appendChild(document.createTextNode(child));
      } else {
        element.appendChild(child);
      }
    });
    return element;
  }

  // Render an input form item
  const renderInputFormItem = (item) => {
    const container = createElement('div');
    const input = createElement('input', {
      type: 'text',
      id: item.modelKeyName,
      name: item.modelKeyName,
      value: item.default || '',
      minlength: item.minLength || undefined,
      maxlength: item.maxLength || undefined,
      pattern: item.pattern || undefined,
      required: item.required ? 'required' : undefined,
    });
    container.appendChild(createElement('label', {}, item.label, input))
    return container;
  }

  // Render a radio form item
  const renderRadioFormItem = (item) => {
    const container = createElement('div');
    item.options.forEach((option) => {
      const radioId = `${item.modelKeyName}_${option.value}`;
      const radio = createElement('input', {
        type: 'radio',
        id: radioId,
        name: item.modelKeyName,
        value: option.value,
        checked: false,
      });
      const label = createElement('label', { for: radioId }, option.label);
      label.addEventListener('click', function() {
        setInputValue(option.value);
      });
      container.appendChild(createElement('div', {}, radio, label));
    });
    return container;
  }

  // Render a checkbox form item
  const renderCheckboxFormItem = (item) => {
    const container = createElement('div');
    item.options.forEach((option) => {
      const checkboxId = `${item.modelKeyName}_${option.value}`;
      const checkbox = createElement('input', {
        type: 'checkbox',
        id: checkboxId,
        name: item.modelKeyName,
        value: option.value,
        checked: false,
      });
      const label = createElement('label', { for: checkboxId }, option.label);
      container.appendChild(createElement('div', {}, checkbox, label));
    });
    return container;
  }

  // Render a select form item
  const renderSelectFormItem = (item) => {
    const select = createElement('select', {
      id: item.modelKeyName,
      name: item.modelKeyName,
      multiple: item.multiple ? 'multiple' : undefined,
    });
    item.options.forEach((option) => {
      const optionElement = createElement('option', {
        value: option.value,
        selected: item.default === option.value ? 'selected' : undefined,
      }, option.label);
      select.appendChild(optionElement);
    });
    return createElement('label', {}, item.label, select);
  }

  // Render an unknown form item
  const renderUnknownFormItem = (item) => {
    return createElement('div', {}, `Unknown item: ${item.desc}`);
  }

  // Main function to render the form
  const renderForm = (formResponse) => {
    const form = createElement('form');
    formResponse.formItems.forEach((item) => {
      let element;
      switch (item.itemType) {
        case 'input':
          element = renderInputFormItem(item);
          break;
        case 'radio':
          element = renderRadioFormItem(item);
          break;
        case 'checkbox':
          element = renderCheckboxFormItem(item);
          break;
        case 'select':
          element = renderSelectFormItem(item);
          break;
        default:
          element = renderUnknownFormItem(item);
      }
      form.appendChild(element);
    });
    return form;
  }

  class CustomForm extends HTMLElement {
    constructor() {
      super();

      // Create a shadow root
      this.attachShadow({ mode: 'open' });

      // Create styles for the form
      const style = document.createElement('style');
      style.textContent = `
        /* Add styles for your form here */
        form {
          /* Example style */
          margin: 16px;
          padding: 16px;
          border: 1px solid #ccc;
          border-radius: 4px;
        }
        label {
          /* Example style */
          display: inline-block;
          margin-top: 8px;
        }
      `;

      this.shadowRoot.append(style);
    }

    // Getter and setter for the formItems property
    get formItems() {
      return this._formItems;
    }

    set formItems(value) {
      if (typeof value === 'string') {
        this._formItems = JSON.parse(value);
      } else if (typeof value === 'object') {
        this._formItems = value;
      }
      this.render();
    }

    // Method to render the form
    render() {
      // Clear the current contents
      this.shadowRoot.innerHTML = '<style>' + this.shadowRoot.querySelector('style').textContent + '</style>';

      // Add the form element
      const formElement = renderForm({ formItems: this._formItems });
      this.shadowRoot.appendChild(formElement);
    }

    // Called when the element is inserted into the DOM
    connectedCallback() {
      if (!this.hasAttribute('role')) {
        this.setAttribute('role', 'form');
      }
      if (this._formItems) {
        this.render();
      }
    }

    // Called when the element is removed from the DOM
    disconnectedCallback() {
      // Cleanup if necessary
    }

    // Respond to attribute changes
    static get observedAttributes() {
      return ['form-items'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
      // Handle changes to the 'form-items' attribute
      if (name === 'form-items') {
        this.formItems = JSON.parse(newValue);
      }
    }
  }

  // Define the new element
  customElements.define('custom-form', CustomForm);
}
