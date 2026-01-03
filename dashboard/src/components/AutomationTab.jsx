import { useState } from 'react';
import ScheduledJobs from './ScheduledJobs';
import RecoveryRecommendations from './RecoveryRecommendations';

export default function AutomationTab() {
  const [activeSubTab, setActiveSubTab] = useState('jobs');

  const tabs = [
    { id: 'jobs', name: 'Scheduled Jobs', icon: '📅' },
    { id: 'recommendations', name: 'Recovery Actions', icon: '💡' },
  ];

  return (
    <div className="space-y-6">
      {/* Sub-tabs */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Sub-tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveSubTab(tab.id)}
                className={`${
                  activeSubTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                } whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2`}
              >
                <span>{tab.icon}</span>
                <span>{tab.name}</span>
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Tab Content */}
      {activeSubTab === 'jobs' && <ScheduledJobs />}
      {activeSubTab === 'recommendations' && <RecoveryRecommendations />}
    </div>
  );
}
