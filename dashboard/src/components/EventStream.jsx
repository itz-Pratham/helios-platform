import React from 'react';

const EventBadge = ({ source }) => {
  const colors = {
    aws: 'bg-yellow-100 text-yellow-800',
    gcp: 'bg-green-100 text-green-800',
    azure: 'bg-purple-100 text-purple-800',
    direct: 'bg-blue-100 text-blue-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
        colors[source] || colors.direct
      }`}
    >
      {source.toUpperCase()}
    </span>
  );
};

const EventStream = ({ events, maxHeight = '600px' }) => {
  if (!events || events.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">
          Live Event Stream
        </h2>
        <div className="flex items-center justify-center h-64 text-gray-400">
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <p className="text-sm">Waiting for events...</p>
            <p className="text-xs mt-2">Events will appear here in real-time</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-gray-900">Live Event Stream</h2>
        <div className="flex items-center text-green-500">
          <span className="relative flex h-3 w-3 mr-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          <span className="text-sm font-medium">Live</span>
        </div>
      </div>

      <div
        className="overflow-y-auto space-y-3"
        style={{ maxHeight }}
      >
        {events.map((event, index) => (
          <div
            key={event.event_id || index}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-gray-50"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <EventBadge source={event.source} />
                  <span className="text-sm font-semibold text-gray-900">
                    {event.event_type}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(event.ingested_at || Date.now()).toLocaleTimeString()}
                  </span>
                </div>

                <div className="text-sm text-gray-600 space-y-1">
                  {event.payload?.order_id && (
                    <div>
                      <span className="font-medium">Order ID:</span>{' '}
                      <span className="font-mono text-xs">{event.payload.order_id}</span>
                    </div>
                  )}
                  {event.payload?.customer_id && (
                    <div>
                      <span className="font-medium">Customer ID:</span>{' '}
                      <span className="font-mono text-xs">{event.payload.customer_id}</span>
                    </div>
                  )}
                  {event.payload?.amount && (
                    <div>
                      <span className="font-medium">Amount:</span>{' '}
                      <span className="text-green-600 font-semibold">
                        ${event.payload.amount}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="ml-4">
                <button
                  className="text-gray-400 hover:text-gray-600"
                  onClick={() => console.log(event)}
                  title="View raw event"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EventStream;
