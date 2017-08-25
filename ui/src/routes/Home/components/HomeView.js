import _ from 'lodash'
import React, { Component } from 'react'
import { browserHistory } from 'react-router'
import { Icon } from 'react-fa'

let backgroundImage = require('../../../assets/clix-i2c-flowers4.svg')

class HomeView extends Component {
  constructor (props) {
    super(props)
    this.state = {
      englishUserSelectStrings: ['teacher', 'student', 'visitor', 'demonstration']
    }
  }

  componentDidMount () {
    // flush the cache because we don't want modules
    // being cached forever...in case someone loads
    // new ones, we need to refresh the value in state
    console.log('home view mounting')
    this.props.onFlush()
    this.props.onGetConfiguration()
    this.props.onGetModules()
  }

  componentDidUpdate (prevProps, prevState) {
    if (!this.props.modules) {
      this.props.onGetModules()
    }
    if (!this.props.locale && !this.props.hasConfiguration) {
      this.props.onGetConfiguration()
    }
  }

  // This seems horrible
  _getEnglishUserType = () => {
    // find by index
    let matchIndex = this.userSelectStrings.indexOf(this.props.survey.userType)
    if (matchIndex >= 0) {
      return this.state.englishUserSelectStrings[matchIndex]
    } else {
      return null
    }
  }

  renderUserTypeButtons = (label, index) => {
    let className = 'user-select'
    let checked = false
    if (this.props.survey && this.props.survey.userType === label) {
      className = 'user-select button-gradient-active'
      checked = true
    }
    return (
      <div className={className}>
        <label key={index}
          htmlFor={label}>
          <input key={index}
            id={label}
            onChange={(e) => this._onHandleUserTypeSelect(e)}
            type='radio'
            name='userType'
            value={label}
            checked={checked}
            className='user-select__input'
            ref={(input) => { this.inputField = input }}
            />
          {label}
        </label>
      </div>
    )
  }

  renderUserCountButtons = (label, index) => {
    let className = 'count-select'
    let checked = false
    if (this.props.survey && this.props.survey.userCount === label) {
      className = 'count-select button-gradient-active'
      checked = true
    }
    return (
      <div className={className}>
        <label key={index}
          htmlFor={label}>
          <input key={index}
            onChange={(e) => this._onHandleUserCountSelect(e)}
            type='radio'
            name='userCount'
            value={label}
            id={label}
            checked={checked} />
          {label}
        </label>
      </div>
    )
  }

  render () {
    if (!this.props.locale) {
      return (
        <div>
          <h1>Please set your school configuration at this <a href='/school'>link</a>.</h1>
        </div>
      )
    }

    this.userSelectStrings = [this.props.strings.splash.teacher,
      this.props.strings.splash.student,
      this.props.strings.splash.visitor,
      this.props.strings.splash.demonstration]
    let userCount
    if (this.props.survey && this.props.survey.userType && this._getEnglishUserType() !== 'demonstration') {
      userCount = (
        <form action='' className='count-select-form'>
          <fieldset>
            <legend>
              <h2 className='pg-subtitle'>{this.props.strings.splash.prompt}</h2>
            </legend>
            <article className='but-select'>
              {_.map(['1', '2', '3', '3+'], this.renderUserCountButtons)}
            </article>
          </fieldset>
        </form>
      )
    }

    let submitButton

    if (this.props.survey &&
        this.props.survey.userType &&
      (this.props.survey.userCount || this._getEnglishUserType() === 'demonstration')) {
      submitButton = (
        <button className='hi-but'
          onClick={this._onHandleSubmit}
          // style={[styles.button, styles.userSelectButton, styles.submitButton]}
          >
          {this.props.strings.breadcrumbs.selectSubject}&nbsp;&nbsp;
          <Icon name='chevron-right' aria-hidden={true} /></button>
      )
    }
    return (
      <div className='gradient-wrapper'>
        <img src={backgroundImage} alt='' className='gradient-wrapper__image' />

        <main className='span_11_of_12 main-content homeview__content'>
          <h1 className='pg-title'>{this.props.strings.splash.title}</h1>
          <form action='' className='user-select-form'>
            <fieldset>
              <legend>
                <h2 className='pg-subtitle'>{this.props.strings.splash.subtitle}</h2>
              </legend>
              <article className='but-select'>
                {_.map(this.userSelectStrings, this.renderUserTypeButtons)}
              </article>
            </fieldset>
          </form>
          {userCount}
          {submitButton}
        </main>
      </div>
    )
  }

  _onHandleUserTypeSelect = (e) => {
    console.log('updating survey')
    this.props.onUpdateSurvey({
      userType: e.currentTarget.value
    })
  }

  _onHandleUserCountSelect = (e) => {
    this.props.onUpdateSurvey({
      userType: this.props.survey.userType,
      userCount: e.currentTarget.value
    })
  }

  _onHandleSubmit = () => {
    this.props.onSetSurvey({
      userType: this._getEnglishUserType(),
      userCount: this.props.survey.userCount
    })
    browserHistory.push('/subjects')
  }
}

export default HomeView
