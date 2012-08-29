var SWING_MARGIN_PCT    = 6;
var POLL_DEFAULT_MARGIN = 4;

// bahhh how does Math not have sign builtin?
_sign = function(x) {
  if (x < 0) return -1;
  if (x > 0) return  1;
  return 0;
}

function flatten(nested) {
  return nested.reduce(function (prev,curr) {
    return prev.concat(curr.values);
  },[]);
}
var internalDateFormat = d3.time.format("%Y-%m-%d");
function getDate(dateString) {
  var dateSplit = dateString.split('-');
  //return new Date(Date.UTC(parseInt(dateSplit[0]),parseInt(dateSplit[1]),parseInt(dateSplit[2]),-2,0,0));
  return internalDateFormat.parse(dateString);
}


// calculates the a-priori type of state (swing / safe, if swing adds the type)
// a safe state has voted the same in the last two election by a margin larger than SWING_MARGIN_PCT
// wikipedia article http://en.wikipedia.org/wiki/Swing_state uses 6 pct as the safe/swing differentiator
function calculateStateApriori(state) {
  if (state[2004][0] == state[2008][0] &&
      state[2004][1][0]-state[2004][1][1] > SWING_MARGIN_PCT &&
      state[2008][1][0]-state[2008][1][1] > SWING_MARGIN_PCT)
    state.apriori = state[2004][0] + ' Safe';
  else
    state.apriori = 'Unknown'; // Swing states have unknown outcomes
}

function calculatePollOutcome(poll) {
  var pollValue = 'Unknown';
  var margin    = poll.margin || POLL_DEFAULT_MARGIN;
  var swing     = Math.abs(poll.results.lead_margin) < margin;
  var winner    = 'Unknown';
  if (poll.results.lead_margin>0)
      winner = 'Republican';
  if (poll.results.lead_margin<0)
      winner = 'Democratic';
  if (winner != 'Unknown') {
      pollValue = winner;
      if (swing)
          pollValue += ' Swing';
      else
          pollValue += ' Safe';
  }
  poll.outcome = pollValue;
}

// TODO: need to use finish using preferences to choose polls
function choosePoll(polls) {
  var allpolls      = polls.reduce(function (prev,curr) {
    return prev.concat(curr);
  },[]);
  // stores all removed polls
  var removedpolls  = [];
  var avgpolls      = [];

  // choose by voter type
  var nestedByVoterType = d3.nest().key(function (d) {return d.votertype;})
                                   .entries(allpolls);
  var nestedallpolls=nestedByVoterType.filter(function (pollgrp) {
    var result = preferences.votertypes.use[pollgrp.key];
    if (!result) {
      removedpolls.concat(pollgrp.values);
    }
    return result;
  });

  // need to choose or average
  // if (nestedallpolls.length>1) {
  //   var choicepref = preferences.votertypes.choice;
  //   if (choicepref == 'RV') {
  //     delete nestedallpolls['LV'];
  //   }
  //   if (choicepref == 'LV') {
  //     delete nestedallpolls['RV'];
  //   }
  // }    
  // flatten remaining polls
  var polllist = nestedallpolls.reduce(function (prev,curr) {
    return prev.concat(curr.values);
  },[]);

  if (polllist.length>1) {
    avgpolls=polllist;
    var avglead   = d3.mean(polllist,function(poll) {return poll.results.lead_margin;});
    var aggerror  = d3.round(
                      Math.sqrt(
                        d3.sum(polllist,
                          function(poll) {
                            return Math.pow(poll.margin,2);
                          })
                        ),2); 
    allpolls = [{ margin:aggerror,
                  toDate:polllist[0].toDate,
                  results:{ 
                    democrat:polllist[0].results.democrat,
                    republican:polllist[0].results.republican,
                    lead_margin:avglead}}];
  } else {
    allpolls = polllist;
  }
  if (removedpolls.length>1) {
  }
  if (avgpolls.length>1) {
  }
  return allpolls.slice(preferences.polltype)[0];
}

// some states have multiple polls ending on the same day
// sometimes these polls have different sampling types
// - Registered Voters (RV) vs Likely Voters (LV)
// - Different pollers (e.g. Rasmussen vs Gallup)
// if they have different outcomes, we should choose one (since each outcome has it's own bucket)
function processPolls(stateData) {
  var nestedByEndDay  = d3.nest()
                          .key(function (poll) {return poll.toDate;})
                          .entries(stateData.polls);
  nestedByEndDay.forEach(function(polledday) {
    polledday.result = choosePoll(polledday.values);
    if(polledday.result != undefined) {
      calculatePollOutcome(polledday.result);
    }
  });
  return nestedByEndDay
          .filter(function (dayData) {return dayData.result != undefined})
          .map(function (dayData) {return dayData.result})
          .sort(function (poll1,poll2) {
            return _sign(poll1.toDate-poll2.toDate);
          });
}

function extendLastPoll(polls,enddate) {
  var lastPollResult = polls.slice(-1)[0];

  interpolated_range = d3.time.day.range(d3.time.day.offset(lastPollResult.date,1),enddate)
                                  .map(function(d) { 
                                        return {state:lastPollResult.state,
                                                date:d,
                                                value:lastPollResult.value,
                                                outcome:lastPollResult.outcome};}
                                      );
  return polls.concat(interpolated_range)
}

// generate a timeline from jan 1st until the current day of predicted state outcome for a state
function generateDaily(stateData) {
  calculateStateApriori(stateData);
  var processedPolls = processPolls(stateData);
  dailyData = processedPolls.reduce(function (previousResults,currentPoll) {
      var lastPollResult = previousResults.slice(-1)[0];

      var pollDate = currentPoll.toDate;
      var pollOutcome = currentPoll.outcome;

      var newResult = extendLastPoll(previousResults,pollDate);
      newResult.push({state:stateData.name,date:pollDate,
                      outcome:pollOutcome,value:stateData.votes});
      
      return newResult;
  },[{state:stateData.name,date:getDate('2012-01-01'),
      outcome:stateData.apriori,value:stateData.votes}]) 
  return extendLastPoll(dailyData,new Date());
}

// generate the timelines of all states
function generateStateData() {
  return window.data.concat(window.UNKNOWN_STATES).map(function (state) {return generateDaily(state);});
}

// aggregate by category from the state timelines
function generateCategoryData() {
  var dataByState           = generateStateData();
  var flattenedPollResults  = dataByState.reduce(function (previousStates,currentState) {
    return previousStates.concat(currentState);
  },[]);
  var nestedByPollDayResult = d3.nest()
                                .key(function (poll) { return poll.outcome;})
                                .key(function (poll) { return poll.date;})
                                .entries(flattenedPollResults);
  nestedByPollDayResult.forEach(function (outcome) {
    // calculate total for each day
    outcome.values.forEach(function (outComeDay) {
      outComeDay.value = outComeDay.values.reduce(function (previous,current) {
                                                    return previous+current.value;
                                                  },0);
    });

    // fill in missing days
    //  step 1: sort
    outcome.values.sort(function (day1,day2) {
      return _sign((new Date(day1.key)) - (new Date(day2.key)));
    });

    //  step 2: fill in the blanks
    outcome.values = outcome.values.reduce(
      function (prev,curr) {
        var last = prev.slice(-1)[0];
        curr['date'] = new Date(curr.key);              
        curr['key']=outcome.key;
        var interpolated_blank = d3.time.days( d3.time.day.offset(
                                                  new Date(last.date),1),
                                               new Date(curr.date))
                                        .map(function (d) {
                                            return {key:outcome.key,
                                                    date:d,
                                                    value:0};
                                          });
        var newprevious = prev.concat(interpolated_blank);              
        newprevious.push(curr);
        return newprevious;
    },[{date:getDate("2011-12-31"),value:0,key:outcome.key}]).splice(1);

    // pad the end
    var last = outcome.values.slice(-1)[0];
    var lastDate = last.date;
    var today = new Date();
    var interpolated_end = d3.time.days(d3.time.day.offset(lastDate,1),
                                        d3.time.day.offset(today,-1))
                                  .map(function (d) {
                                    return {date:d,
                                            value:0,
                                            key:outcome.key};
                                  });
    outcome.values = outcome.values.concat(interpolated_end);
    outcome.values = outcome.values.slice(0,
      d3.time.days(getDate("2012-01-01"),
                   d3.time.day.offset(today,-1)).length);
  });
  return nestedByPollDayResult;
}

stack = d3.layout.stack()
    .offset("zero")
    .values(function(d) { return d.values; })
    .x(function(d) { return d.date; })
    .y(function(d) { return d.value; });


function calculateData() {
  sdata = generateCategoryData();
  var sortorder   = { 'Republican Safe':5, 
                      'Republican Swing':4,
                      'Unknown':3,
                      'Democratic Swing':2,
                      'Democratic Safe':1
                    };
  for (var datatype in sortorder) {
    if (sdata.filter(function (d) {return d.key==datatype;}).length==0) {
      var newarray = {};
      newarray.key = datatype;
      newarray.values = sdata[0].values.map(function (el) {
        return {date:el.date,key:datatype,value:0};
      });
      sdata.push(newarray);
    }
  }
  sdata.sort(function (l,r) {
    return _sign(sortorder[l.key]-sortorder[r.key]);
  });
  
  fdata = flatten(sdata);
  layers = stack(sdata);

}

function getLVRVuseprefs() {
  preferences.votertypes.use.RV = document.getElementById("LVRV_RV").checked;  
  preferences.votertypes.use.LV = document.getElementById("LVRV_LV").checked;  
  preferences.votertypes.use.UK = document.getElementById("LVRV_UK").checked;    
}

function LVRVuse(choicetype) {
  getLVRVuseprefs();
  transition();
}

function LVRVchoice(choicetype) {
  preferences.votertypes.choice=choicetype;
  transition();
}

function transition() {
  duration = 1500;
  calculateData();
  d3.selectAll(".layer")
  .data(layers)
  .transition()
  .duration(duration)
  .attr("d",function(d) { return area(d.values);})
  .attr("fill", function (d, i) { return z(i); });
}
