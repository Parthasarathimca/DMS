import { browser, by, element } from 'protractor';

export class UiPage {
  navigateTo() {
    return browser.get('/');
  }

  getParagraphText() {
    return element(by.css('ui-root h1')).getText();
  }
}
